import logging
import pymupdf
from src.Utils.TextCleaner import TextCleaner

class ExtrairDadosPdfService:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_text_from_pdf(self, file_path, start_page=0, end_page=None):
        doc = pymupdf.open(file_path)
        total_paginas = len(doc)
        self.logger.info(f"📚 PDF aberto: {file_path} | Total: {total_paginas} pgs")
        
        if end_page is None or end_page > total_paginas:
            end_page = total_paginas
            
        for page_num in range(start_page, end_page):
            p_num_display = page_num + 1
            self.logger.info(f"📑 [Pág {p_num_display}] Extraindo blocos de texto...")

            page = doc.load_page(page_num)
            
            # "blocks" preserva melhor a estrutura de parágrafos do livro
            blocos = page.get_text("blocks")
            
            # Pegamos o texto bruto de todos os blocos sem filtros agressivos aqui
            # b[4] é o conteúdo de texto do bloco no PyMuPDF
            texto_bruto = "\n".join([b[4] for b in blocos]).strip()

            if not texto_bruto:
                self.logger.warning(f"⚠️ [Pág {p_num_display}] Nenhum texto encontrado (página pode ser uma imagem/diagrama).")
            else:
                self.logger.info(f"✅ [Pág {p_num_display}] Extração concluída ({len(texto_bruto)} caracteres).")

            # Entrega o conteúdo bruto para que os serviços seguintes decidam o que fazer
            yield {
                "numero_pagina": p_num_display,
                "conteudo": texto_bruto
            }
            
        doc.close()
        self.logger.info("🏁 Fluxo de extração finalizado.")