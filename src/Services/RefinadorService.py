
import os
import logging
import llama_cpp

class RefinadorService:
    def __init__(self, model_path: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Arquivo do modelo não encontrado: {model_path}")

        self.logger.info("Carregando modelo local para refinamento...")
        
        self.llm = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1, # Usa todas as camadas da GPU disponíveis
            n_batch=512, # Processa o texto em blocos menores
            n_threads = min(4, os.cpu_count() // 2),
            verbose=False # Deixa o console limpo
        )

    def refinar_traducao(self, texto_original, texto_traduzido):
        """
        Usa o Phi-3 para comparar o original e o traduzido,
        ajustando termos técnicos e limpando ruídos.
        """
        # Formato de Prompt específico do Phi-3
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
                    Você é um Revisor Técnico Bilíngue especialista em livros de TI e Gestão.
                    Sua tarefa é refinar a TRADUÇÃO ATUAL baseando-se no TEXTO ORIGINAL.

                    REGRAS CRÍTICAS:
                    1. TÍTULO: Se esta página inicia um NOVO capítulo ou seção importante, comece com '### Título'. Se for continuação de um texto anterior, NÃO repita o título.
                    2. TERMINOLOGIA: Mantenha termos técnicos de mercado (ex: Stakeholders, Pipeline, Design Patterns) se a tradução soar artificial, mas garanta que o contexto seja PT-BR.
                    3. FLUIDEZ: Remova vícios de tradução literal (ex: "fazer sentido" em vez de "make sense").
                    4. RESPOSTA: Retorne APENAS o texto revisado. Não explique suas alterações.<|eot_id|>
                    <|start_header_id|>user<|end_header_id|>
                    TEXTO ORIGINAL: {texto_original}
                    TRADUÇÃO ATUAL: {texto_traduzido}<|eot_id|>
                    <|start_header_id|>assistant<|end_header_id|>"""

        response = self.llm(
            prompt,
            max_tokens=len(texto_traduzido) + 200, # Permite expansão leve
            temperature=0.2, # Baixa para evitar que a IA invente coisas
            top_p=0.9,
            repeat_penalty=1.3,
            stop=["<|eot_id|>", "<|end_of_text|>", "TEXTO ORIGINAL:", "TRADUÇÃO ATUAL:"]
        )
        texto_final = response["choices"][0]["text"].strip()
        # Limpeza de segurança: Caso o LLM repita o sistema de headers
        texto_final = texto_final.replace("<|start_header_id|>assistant<|end_header_id|>", "")
        return texto_final
    
    def reestruturar_sumario(self, texto_sumario):
        prompt = f"""<|start_header_id|>system<|end_header_id|>
        Você é um assistente especializado em estruturação de documentos.
        Sua tarefa é converter um texto de SUMÁRIO extraído de um PDF em uma lista Markdown organizada.

        REGRAS:
        1. Use '*' para itens principais e indentação (4 espaços) para sub-itens.
        2. Remova pontos excessivos (ex: .........).
        3. Preserve os números das páginas à direita.
        4. Traduza os títulos para o Português, mantendo a terminologia técnica de TI.
        5. Retorne APENAS o Markdown da lista.<|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        TEXTO DO SUMÁRIO:
        {texto_sumario}<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>"""
                
        resposta_completa = self.llm(prompt, max_tokens=2048, stop=["<|eot_id|>"])
        
        if isinstance(resposta_completa, dict):
            texto_final = resposta_completa['choices'][0]['text']
        else:
            texto_final = str(resposta_completa)
            
        return texto_final.strip()