import re

class TextCleaner:

    @staticmethod
    def limpar_extração_pdf(texto: str) -> str:
        if not texto: return ""
        
        linhas = texto.split('\n')
        if len(linhas) > 1 and len(linhas[0].strip()) < 50:
            # Se a primeira linha parece um título de cabeçalho, removemos
            linhas.pop(0)
            texto = '\n'.join(linhas)

        # 1. Remove números de página isolados (ex: "\n 42 \n")
        texto = re.sub(r'\n\s*\d+\s*\n', '\n', texto)
        
        # 2. Remove hifens de quebra de linha (soft- \n ware -> software)
        texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
        
        # 3. Transforma quebras de linha simples em espaços, mas PRESERVA parágrafos
        # Técnica: substitui \n\n por um token temporário, limpa \n simples, e volta o token
        texto = re.sub(r'\n\s*\n', '[[PARAGRAPH]]', texto)
        texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
        texto = texto.replace('[[PARAGRAPH]]', '\n\n')
        
        # 4. Remove múltiplos espaços e caracteres especiais de controle
        texto = re.sub(r'[ \t]+', ' ', texto)
        texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)
        
        return texto.strip()

    @staticmethod
    def identificar_tipo_conteudo(texto: str) -> str:
        """
        Identifica se o texto é SUMARIO, CODIGO ou TEXTO_TECNICO.
        """
        texto_lower = texto.lower()
        indicadores_sumario = {'contents', 'table of contents', 'index', 'sumário', 'índice'}
        
        # Se tiver indicadores de sumário ou muitos pontos de guia
        if any(item in texto_lower for item in indicadores_sumario) or texto.count('....') > 5:
            return "SUMARIO"
        
        # Se tiver estrutura de código
        if texto.count('{') > 5 and texto.count(';') > 5:
            return "CODIGO"
            
        return "TEXTO_TECNICO"
    
    @staticmethod
    def limpar_sujeira_digital(texto: str) -> str:
        """
        Remove links e frases de marketing que poluem a tradução.
        """
        if not texto:
            return ""
        
        # 1. Regex de URL mais abrangente (pega links entre parênteses e no final de frases)
        # Remove http, https, www e links que terminam em .com, .net, .org, etc.
        padrao_url = r'(https?://\S+|www\.\S+|\b\S+\.(?:com|net|org|edu|gov|io|me)\b(/\S*)?)'
        texto = re.sub(padrao_url, '', texto, flags=re.IGNORECASE)

        # 2. Lista de "Stop Words" de propaganda (Call to Action)
        # Adicionei termos comuns em PDFs de bibliotecas digitais e sites de download
        padroes_sujeira = [
            r'click here', r'buy now', r'visit our website', 
            r'available at', r'downloaded from', r'all rights reserved',
            r'copyright ©', r'free ebook', r'subscribe to',
            r'scan this qr', r'get more books'
        ]
        
        for padrao in padroes_sujeira:
            # O \b garante que ele pegue a frase inteira, não partes de palavras
            texto = re.sub(rf'\b{padrao}\b', '', texto, flags=re.IGNORECASE)

        # 3. Limpeza Final: Remove espaços múltiplos e linhas vazias que sobraram
        texto = re.sub(r' +', ' ', texto) # Remove espaços duplos
        texto = re.sub(r'\n\s*\n', '\n\n', texto) # Remove múltiplas quebras de linha

        return texto.strip()

    @staticmethod
    def texto_parece_propaganda(texto: str) -> bool:
        """
        Retorna True se a página tem alta densidade de links ou termos de lixo,
        indicando que a página inteira pode ser descartada.
        """
        if not texto or len(texto.strip()) < 50:
            return True # Páginas quase vazias são irrelevantes

        texto_lower = texto.lower()
        
        # Conta ocorrências de indicadores de lixo
        termos_lixo = ['downloaded from', 'click here', 'visit our', 'all rights reserved', 'www.']
        pontuacao_lixo = sum(1 for termo in termos_lixo if termo in texto_lower)
        
        # Se tiver mais de 2 indicadores em uma página curta, é propaganda
        if pontuacao_lixo >= 2 and len(texto) < 600:
            return True
            
        return False

    @staticmethod
    def calcular_confiabilidade(original, traduzido_ia):
        """
        Retorna True se a tradução parece legítima, False se houver sinais de delírio.
        """
        # Proteção contra strings vazias ou None (Evita DivisionByZero)
        if not original or len(original.strip()) == 0:
            # Se o original é vazio, a tradução também deve ser curta/vazia
            return len(traduzido_ia.strip()) < 50 

        # 1. Detecção de lixo repetitivo
        if re.search(r'(\w{2,})\1{5,}', traduzido_ia): 
            return False
            
        # 2. Detecção de loops de caracteres (ex: 2.2.2.2 ou ....)
        if traduzido_ia.count('.') > (original.count('.') + 30):
            return False

        # 3. Detecção de Idioma (Sinal de que ele repetiu o inglês)
        palavras_ingles = {'the', 'of', 'and', 'to', 'in', 'is', 'that'}
        palavras_texto = set(traduzido_ia.lower().split())
        if len(palavras_texto.intersection(palavras_ingles)) > 10:
            return False

        # 4. Proporção de tamanho (Agora protegida contra divisão por zero)
        # Usamos max(1, len(original)) como segurança extra, embora o 'if' acima já resolva
        proporcao = len(traduzido_ia) / len(original)
        if proporcao > 1.8 or proporcao < 0.5: 
            return False           
        return True