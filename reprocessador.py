from src.Services.MarkdownEnhancer import GenericMarkdownEnhancer

def main():
    enhancer = GenericMarkdownEnhancer('traducao_final.md')
    enhancer.process_and_view('livro_com_referencia.html')
    

if __name__ == "__main__":
    main()