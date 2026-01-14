import gc
import logging
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from src.Services.MarkdownEnhancer import GenericMarkdownEnhancer
from src.Utils.TextCleaner import TextCleaner

class ProcessadorTraducaoService:

    def __init__(self, argo_translate_service, refinador_service, arquivo_saida="traducao_final.md"):
        self.argo_translate_service = argo_translate_service
        self.refinador_service = refinador_service
        self.arquivo_saida = arquivo_saida
        self.logger = logging.getLogger(self.__class__.__name__)
        self.file_lock = threading.Lock()
        self.llm_lock = threading.Lock()
        # Estilo CSS para injetar no início do arquivo
        self.STYLE = """<style>body { max-width: 900px; margin: 0 auto; padding: 2rem; font-family: sans-serif; line-height: 1.6; color: #1f2328; background: #fff; } h2 { border-bottom: 1px solid #d0d7de; padding-bottom: 8px; margin-top: 40px; } @media (prefers-color-scheme: dark) { body { background: #0d1117; color: #e6edf3; } h2 { border-bottom-color: #30363d; } }</style><meta name="viewport" content="width=device-width, initial-scale=1.0">"""

    def processar_livro_incremental(self, gerador_paginas, total_paginas=None):
        self.logger.info("🚀 Iniciando Pipeline Otimizada...")
        
        # 1. Preparação do Arquivo
        with open(self.arquivo_saida, "w", encoding="utf-8") as f:
            f.write(self.STYLE + "\n\n# Tradução Processada\n\n<div id='Sumario'></div>\n\n")

        concluidas = 0
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for pagina_original in gerador_paginas:
                p_num = pagina_original['numero_pagina']
                
                conteudo_limpo = TextCleaner.limpar_extração_pdf(pagina_original['conteudo'])
                pagina_original['conteudo'] = conteudo_limpo

                self.logger.info(f"⏳ [Pág {p_num}] Traduzindo base (Argos)...")
                
                pagina_traduzida = self.argo_translate_service.traduzir_pagina(pagina_original)
                
                self.logger.info(f"🧠 [Pág {p_num}] Enviando para refinamento LLM (GPU)...")
                fut = executor.submit(self._refinar_e_gravar, pagina_traduzida, pagina_original['conteudo'])
                futures.append(fut)

                # Callback para atualizar progresso assim que a página for gravada
                def callback_concluido(f, num=p_num):
                    nonlocal concluidas
                    concluidas += 1
                    status = "✅" if not f.exception() else "❌"
                    # Se você souber o total de páginas, pode exibir a %
                    progresso_str = f"({concluidas}/{total_paginas})" if total_paginas else f"({concluidas} pgs)"
                    self.logger.info(f"{status} [Pág {num}] Processamento concluído {progresso_str}")

                fut.add_done_callback(callback_concluido)

                # Controle de fluxo para não estourar a VRAM
                if len(futures) > 10:
                    concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    # Limpeza de lista de futuros terminados
                    futures = [f for f in futures if not f.done()]
                    gc.collect()
            if futures:
                self.logger.info("🏁 Aguardando finalização das últimas páginas...")
                concurrent.futures.wait(futures)
            
        self.logger.info("✨ Processamento completo! Arquivo gerado com sucesso.")
        self.finalizar_processamento()

    def _refinar_e_gravar(self, pagina_traduzida, original):
        try:
            p_num = pagina_traduzida['pagina']
            tipo = pagina_traduzida.get('tipo_conteudo', 'TEXTO_TECNICO')
            
            if pagina_traduzida.get('ignorar'):
                self.logger.warning(f"⚠️ [Pág {p_num}] Descartada por filtros de ruído.")
                return

            conteudo_base_argos = pagina_traduzida['traduzido']
            conteudo_final = ""

            # LÓGICA DE REFINAMENTO POR TIPO
            with self.llm_lock:
                if tipo == "SUMARIO":
                    self.logger.info(f"📊 [Pág {p_num}] Reestruturando hierarquia do Sumário...")
                    conteudo_final = self.refinador_service.reestruturar_sumario(conteudo_base_argos)
                
                elif tipo == "CODIGO":
                    self.logger.info(f"💻 [Pág {p_num}] Código detectado. Preservando original.")
                    conteudo_final = f"```\n{original}\n```"
                
                else:
                    self.logger.info(f"🧠 [Pág {p_num}] Refinando tradução técnica...")
                    refinado = self.refinador_service.refinar_traducao(original, conteudo_base_argos)
                    
                    # Validação de Confiabilidade (apenas para texto comum)
                    if TextCleaner.calcular_confiabilidade(original, refinado):
                        conteudo_final = refinado
                    else:
                        self.logger.warning(f"⚠️ [Pág {p_num}] Refinamento instável. Usando base Argos.")
                        conteudo_final = conteudo_base_argos

            # Escrita no arquivo (Thread-safe)
            with self.file_lock:
                with open(self.arquivo_saida, "a", encoding="utf-8") as f:
                    f.write(f'\n## Página {p_num} <a id="pg{p_num}"></a>\n\n')
                    f.write(f"{conteudo_final}\n\n")
                    f.write(f'[↑ Voltar ao topo](#Sumario)\n')
                    f.write("\n---\n")
                    f.flush()

            # --- LIMPEZA DE MEMÓRIA ---
            pagina_traduzida['traduzido'] = ""
            del conteudo_final
            del original
            gc.collect()

        except Exception as e:
            self.logger.error(f"❌ Falha crítica na Página {p_num}: {e}")

    def finalizar_processamento(self):
        self.logger.info("📦 Consolidando arquivos e gerando HTML...")
        caminho_md = self.arquivo_saida 
        caminho_html = caminho_md.replace('.md', '.html')
        try:
            enhancer = GenericMarkdownEnhancer(caminho_md)
            enhancer.process_and_view(caminho_html)
            self.logger.info(f"✨ Pronto! Link de leitura: {caminho_html}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar o HTML final: {e}")