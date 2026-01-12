import gc
from src.Utils.ArgosManager import ArgosManager
import logging
import argostranslate.translate

class TraducaoArgosPdfService:
    def __init__(self, from_code="en", to_code="pt"):
        self.from_code = from_code
        self.to_code = to_code
        self.logger = logging.getLogger(self.__class__.__name__)

        # Delega a responsabilidade de pacotes para o Manager
        if not ArgosManager.garantir_pacote_instalado(from_code, to_code):
            raise RuntimeError("Não foi possível carregar os pacotes de tradução.")

    def traduzir_pagina(self, item):
        texto = item.get('conteudo', '')
        if not texto.strip():
            return {"pagina": item['numero_pagina'], "traduzido": ""}
        
        max_chunk_size = 1000
        chunks = [texto[i:i + max_chunk_size] for i in range(0, len(texto), max_chunk_size)]
        
        partes_traduzidas = []
        for chunk in chunks:
            try:
                res = argostranslate.translate.translate(chunk, self.from_code, self.to_code)
                partes_traduzidas.append(res)
            except Exception:
                partes_traduzidas.append("[Erro no chunk]")

        resultado = {
            "pagina": item['numero_pagina'],
            "traduzido": " ".join(partes_traduzidas)
        }

        del partes_traduzidas
        gc.collect() # Força a limpeza da memória após processar a página

        return resultado
