import os

# Força o Python a enxergar as pastas do CUDA e do compilador
cuda_bin = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin"
# O VS 2026 usa ferramentas da v145 ou v150, vamos garantir o acesso
vs_bin = r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64"

if os.path.exists(cuda_bin):
    os.add_dll_directory(cuda_bin)
if os.path.exists(vs_bin):
    os.add_dll_directory(vs_bin)

# Adiciona ao PATH para compatibilidade com versões antigas do Python
os.environ["PATH"] = cuda_bin + os.pathsep + vs_bin + os.pathsep + os.environ.get("PATH", "")

import logging
from src.Services.ProcessadorTraducaoService import ProcessadorTraducaoService
from src.Services.ExtrairDadosPdfService import ExtrairDadosPdfService
from src.Services.TraducaoArgosPdfService import TraducaoArgosPdfService
from src.Services.RefinadorService import RefinadorService
from src.Config.Logging import LoggingConfig

def main():
    LoggingConfig.configurar_logging()
    logging.getLogger("argostranslate").setLevel(logging.WARNING)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)
    logger = logging.getLogger("Main")

    # 1. Setup de Dependências
    caminho_pdf = "E:\\Books\\97-things-every-software-architect-should-know.pdf"
    caminho_llm = "E:\\Projetos\\Models\\Meta-Llama-3.1-8B-Instruct-Q4_K_L.gguf"
    traducao_base = TraducaoArgosPdfService(from_code="en", to_code="pt")
    refinador = RefinadorService(caminho_llm)
    processador = ProcessadorTraducaoService(traducao_base, refinador, "traducao_final.md")
    
    # 2. Execução
    logger.info("Extraindo PDF...")
    dados = ExtrairDadosPdfService().extract_text_from_pdf(caminho_pdf)
    logger.info("Iniciando Pipeline de Processamento...")
    processador.processar_livro_incremental(dados)

    logger.info("Tudo pronto!")

if __name__ == "__main__":
    main()