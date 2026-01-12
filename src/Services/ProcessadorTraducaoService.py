import gc
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from src.Utils.TextCleaner import TextCleaner

class ProcessadorTraducaoService:

    def __init__(self, traducao_service, refinador_service, arquivo_saida="traducao_final.md"):
        self.traducao_service = traducao_service
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
                
                self.logger.info(f"⏳ [Pág {p_num}] Traduzindo base (Argos)...")
                
                pagina_traduzida = self.traducao_service.traduzir_pagina(pagina_original)
                
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

    def _refinar_e_gravar(self, pagina_traduzida, original):
        try:
            p_num = pagina_traduzida['pagina']
            conteudo_final = ""

            # Lógica de Bypass
            if TextCleaner.precisa_refinamento_llm(original):
                self.logger.info(f"Página {p_num}: Sumário detectado. Ignorando LLM.")
                conteudo_final = pagina_traduzida['traduzido']
            else:
                self.logger.info(f"Refinando Página {p_num} (GPU)...")
                with self.llm_lock:
                    conteudo_final = self.refinador_service.refinar_traducao(original, pagina_traduzida['traduzido'])

            # Escrita no arquivo (Anexando)
            with self.file_lock:
                with open(self.arquivo_saida, "a", encoding="utf-8") as f:
                    f.write(f'\n## Página {p_num} <a id="pg{p_num}"></a>\n\n')
                    f.write(f"{conteudo_final}\n\n")
                    f.write(f'[↑ Voltar ao topo](#Sumario)\n') # Link em MD puro
                    f.write("\n---\n")
                    f.flush()

            # --- LIMPEZA AGRESSIVA ---
            # Removemos referências a strings gigantescas imediatamente
            pagina_traduzida['traduzido'] = ""
            del conteudo_final
            del original
            gc.collect() # Avisa o Python para limpar o lixo da RAM

        except Exception as e:
            self.logger.error(f"Falha crítica na Página {p_num}: {e}")