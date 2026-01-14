import gc
import logging
import argostranslate.translate
from src.Utils.ArgosManager import ArgosManager
from src.Utils.TextCleaner import TextCleaner

class TraducaoArgosPdfService:
    def __init__(self, from_code="en", to_code="pt"):
        self.from_code = from_code
        self.to_code = to_code
        self.logger = logging.getLogger(self.__class__.__name__)

        if not ArgosManager.garantir_pacote_instalado(from_code, to_code):
            raise RuntimeError("Não foi possível carregar os pacotes de tradução.")

    def traduzir_pagina(self, item):
        texto_original = item.get('conteudo', '')
        p_num = item['numero_pagina']

        if not texto_original.strip():
            self.logger.info(f"⚪ [Pág {p_num}] Ignorada: Página totalmente vazia ou sem texto extraível.")
            return {"pagina": p_num, "traduzido": "", "ignorar": True, "tipo_conteudo": "N/A"}

        # Início da higienização
        self.logger.info(f"🧹 [Pág {p_num}] Higienizando texto (Original: {len(texto_original)} chars)...")
        
        texto_higienizado = TextCleaner.limpar_sujeira_digital(texto_original)
        self.logger.debug(f"🔍 [Pág {p_num}] Após limpar_sujeira_digital: {len(texto_higienizado)} chars")

        texto_limpo = TextCleaner.limpar_extração_pdf(texto_higienizado)
        self.logger.info(f"✨ [Pág {p_num}] Limpeza concluída. Texto final: {len(texto_limpo)} chars.")

        # Verificação crítica: Se o texto sumiu após a limpeza
        if len(texto_original) > 10 and len(texto_limpo) < 5:
            self.logger.warning(f"⚠️ [Pág {p_num}] Alerta: A limpeza removeu quase todo o conteúdo!")

        if TextCleaner.texto_parece_propaganda(texto_limpo):
            self.logger.warning(f"🚫 [Pág {p_num}] Ignorada: O algoritmo de limpeza classificou como propaganda/lixo.")
            return {"pagina": p_num, "traduzido": "", "ignorar": True, "tipo_conteudo": "PROPAGANDA"}

        # 3. IDENTIFICAÇÃO DE CONTEUDO
        tipo_conteudo = TextCleaner.identificar_tipo_conteudo(texto_limpo)

        # 4. TRADUÇÃO DOS CHUNKS (Usando o texto já limpo)
        limite = 1000
        chunks = []
        
        texto = texto_limpo
        # Lógica para fatiar sem quebrar palavras
        while len(texto) > 0:
            if len(texto) <= limite:
                chunks.append(texto)
                break
            
            # Procura o último espaço em branco antes do limite
            indice_corte = texto.rfind(' ', 0, limite)
            
            # Se não achar espaço (palavra gigante), corta no limite mesmo
            if indice_corte == -1:
                indice_corte = limite
                
            chunks.append(texto[:indice_corte])
            texto = texto[indice_corte:].lstrip() # Remove o espaço que sobrou no início
        
        partes_traduzidas = []
        for chunk in chunks:
            try:
                res = argostranslate.translate.translate(chunk, self.from_code, self.to_code)
                partes_traduzidas.append(res)
            except Exception:
                partes_traduzidas.append("[Erro no chunk]")

        resultado = {
            "pagina": p_num,
            "traduzido": " ".join(partes_traduzidas),
            "ignorar": False,
            "tipo_conteudo": tipo_conteudo
        }

        # Limpeza agressiva de RAM
        del partes_traduzidas
        del texto_limpo
        gc.collect()

        return resultado