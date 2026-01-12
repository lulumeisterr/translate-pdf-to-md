import logging
import pymupdf
from src.Utils.TextCleaner import TextCleaner

class ExtrairDadosPdfService:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_text_from_pdf(self, file_path, start_page=0, end_page=None):
        doc = pymupdf.open(file_path)
        self.logger.info(f"PDF aberto. Total de páginas: {len(doc)}")
        total_paginas = len(doc)
        
        # Validação do intervalo de páginas
        if end_page is None or end_page > total_paginas:
            end_page = total_paginas
            
        # Itera apenas no range solicitado
        for page_num in range(start_page, end_page):
            page = doc.load_page(page_num)
            
            # Usar "blocks" em vez de "text" ajuda a identificar parágrafos 
            # e evita que o texto venha todo bagunçado em colunas.
            blocos = page.get_text("blocks")
            
            # Limpeza básica: remove blocos muito curtos (geralmente números de página)
            texto_limpo = "\n".join([b[4] for b in blocos if len(b[4].strip()) > 10])

            if TextCleaner.precisa_refinamento_llm(texto_limpo):
                continue
            texto_processado = TextCleaner.limpar_extração_pdf(texto_limpo)

            yield {
                "numero_pagina": page_num + 1,
                "conteudo": texto_processado
            }
        doc.close()