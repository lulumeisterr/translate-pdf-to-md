
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
        Você é um Revisor Técnico Bilíngue. Sua tarefa é comparar a TRADUÇÃO ATUAL com o TEXTO ORIGINAL.

        Diretrizes:
        1. Identifique inconsistências de significado: Se a tradução mudou o conceito técnico, corrija-a.
        2. O texto traduzido deve manter o conceito técnico do original, corrigindo inconsistências.
        3. A tradução sempre ve ser realizada para português brasileiro (PT-BR).
        4. Melhore a sintaxe: Ajuste frases que pareçam "tradução literal do Google" para um português técnico natural.
        5. Verifique a terminologia: Garanta que termos como 'Architect', 'Design' e 'Stakeholders' estejam usados de forma consistente.
        6. Se a tradução já estiver correta e fiel ao original, retorne-a exatamente como está.
        7. Responda APENAS com o texto final adequado, sem comentários explicativos.<|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        TEXTO ORIGINAL: {texto_original}
        TRADUÇÃO ATUAL: {texto_traduzido}<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>"""

        response = self.llm(
            prompt,
            max_tokens=len(texto_traduzido) + 200, # Permite expansão leve
            temperature=0.04, # Baixa para evitar que a IA invente coisas
            top_p=0.9,
            repeat_penalty=1.2,
            stop=["<|eot_id|>", "<|end_of_text|>"]
        )
        return response["choices"][0]["text"].strip()