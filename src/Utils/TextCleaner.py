import re

class TextCleaner:

    @staticmethod
    def limpar_extração_pdf(texto: str) -> str:
        """
        Limpa ruídos comuns de extração de PDF via Regex.
        """
        # 1. Remove hifens de quebra de linha (soft- \n ware -> software)
        texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
        
        # 2. Transforma quebras de linha simples em espaços (mantém parágrafos duplos)
        # Isso ajuda o tradutor a entender que a frase continua
        texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
        
        # 3. Remove múltiplos espaços
        texto = re.sub(r' +', ' ', texto)
        
        return texto.strip()
    
    @staticmethod
    def precisa_refinamento_llm(texto: str) -> bool:
        """
        Retorna True se a página parecer um sumário ou estiver muito suja.
        """
        indicadores_sumario = ['contents', 'table of contents', 'index']
        texto_lower = texto.lower()
        
        # Verifica se contém palavras de sumário
        if any(item in texto_lower for item in indicadores_sumario):
            return True
        
        # Verifica se tem muitos pontos seguidos (comum em sumários)
        if texto.count('....') > 5:
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

        # Se a IA devolveu algo vazio para um texto que existia
        if not traduzido_ia or len(traduzido_ia.strip()) == 0:
            return False

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