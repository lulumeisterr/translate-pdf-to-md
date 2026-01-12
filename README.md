# Documentação de Instalação: llama-cpp-python com Suporte CUDA

Esta documentação descreve o processo de compilação manual da biblioteca llama-cpp-python para habilitar a aceleração por hardware (GPU) em ambientes Windows com hardware NVIDIA.

🛠️ Ambiente Técnico
    GPU: NVIDIA RTX 3050 (Arquitetura Ampere)
    CUDA Toolkit: v13.1
    Compilador: Visual Studio 2026 (v180)
    Linguagem: Python 3.10+

1. Integração Manual CUDA + Visual Studio
Como o CUDA 13.1 pode não reconhecer nativamente o Visual Studio 2026, os arquivos de integração do MSBuild devem ser movidos manualmente para que o compilador C++ entenda as instruções CUDA.

Acesse a pasta de origem:
    C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\extras\visual_studio_integration\MSBuildExtensions

Copie todos os arquivos desta pasta.
Cole na pasta de destino do Visual Studio (v180):
    C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Microsoft\VC\v180\BuildCustomizations


2. Preparação do Terminal (CMD)
As variáveis de ambiente abaixo são temporárias e devem ser definidas na mesma sessão do Prompt de Comando (CMD) onde a instalação será realizada.

:: Limpa tentativas falhas anteriores e cache do pip
python -m pip cache purge

:: Configura o caminho do Toolkit
set CUDAToolkit_ROOT=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1
set PATH=%CUDAToolkit_ROOT%\bin;%PATH%

3. Compilação e Instalação
Para a série RTX 3050, utilizamos a arquitetura 86. Adicionamos a flag de "compilador não suportado" para permitir que o VS 2026 trabalhe com o CUDA 13.1.

DOS

:: Definição de argumentos para o CMake
:: 1. GGML_CUDA=on: Ativa o backend de GPU
:: 2. CMAKE_CUDA_ARCHITECTURES=86: Otimiza para RTX 3050
:: 3. allow-unsupported-compiler: Ignora restrição de versão do Visual Studio

set CMAKE_ARGS=-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_CUDA_FLAGS="-allow-unsupported-compiler"

:: Instalação forçada reconstruindo a biblioteca do zero
python -m pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir


4. Inicialização no Código Python
Devido às restrições de carregamento de DLLs no Windows, é necessário registrar o diretório de binários do CUDA no início do script principal para evitar erros de RuntimeError: Failed to load shared library.

Python

import os
import llama_cpp

# Deve ser executado antes de instanciar a classe Llama
cuda_bin = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin"
if os.path.exists(cuda_bin):
    os.add_dll_directory(cuda_bin)

# Verificação de disponibilidade
print(f"CUDA disponível: {llama_cpp.GGML_CUDA}")

5. Configuração do Modelo para GPU
Para garantir que o modelo utilize a VRAM da RTX 3050, utilize os seguintes parâmetros no serviço:

Parâmetro,Valor,Descrição
n_gpu_layers,-1,Envia todas as camadas do modelo para a GPU.
n_ctx,8192,Tamanho do contexto (janela de memória de texto).
n_batch,512,Número de tokens processados simultaneamente.