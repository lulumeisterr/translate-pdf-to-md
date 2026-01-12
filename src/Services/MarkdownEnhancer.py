import re
import markdown
import gc

class GenericMarkdownEnhancer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.STYLE = """
            <style>
                :root { --bg: #ffffff; --text: #1f2328; --link: #0969da; --border: #d0d7de; --code-bg: #f6f8fa; }
                @media (prefers-color-scheme: dark) {
                    :root { --bg: #0d1117; --text: #e6edf3; --link: #2f81f7; --border: #30363d; --code-bg: #161b22; }
                }
                body { background: var(--bg); color: var(--text); font-family: sans-serif; line-height: 1.6; margin: 0 auto; padding: 2rem; max-width: 900px; }
                .toc-box { background: var(--code-bg); border: 1px solid var(--border); padding: 20px; border-radius: 8px; margin-bottom: 40px; }
                .toc-list { list-style: none; padding-left: 0; }
                .toc-page { font-weight: bold; margin-top: 8px; padding: 4px 0; border-bottom: 1px dotted var(--border); }
                .toc-page a { display: block; }
                .toc-topic { margin-left: 20px; font-size: 0.9em; list-style: disc; color: var(--link); }
                a { color: var(--link); text-decoration: none; }
                a:hover { text-decoration: underline; }
                h1, h2, h3 { scroll-margin-top: 20px; }
                pre { background: var(--code-bg); padding: 1rem; border-radius: 8px; overflow-x: auto; }
            </style>
        """

    def process_and_view(self, html_output_path):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        processed_md_lines = []
        toc_items = [] 

        for i, line in enumerate(lines):
            # Identifica Página (## Página X)
            match_pg = re.match(r'^## Página (\d+)', line)
            # Identifica se a linha já é um tópico (### Título)
            match_topico = re.match(r'^### (.*)', line)

            if match_pg:
                num = match_pg.group(1)
                tid = f"pg{num}"
                
                # --- LÓGICA PARA PEGAR O TÍTULO AO LADO ---
                titulo_extra = ""
                # Percorre as próximas 5 linhas para achar o primeiro texto que não seja vazio ou meta-tag
                for next_line in lines[i+1 : i+6]:
                    clean = next_line.strip()
                    # Ignora linhas vazias, tags HTML ou linhas de separação
                    if clean and not clean.startswith('<') and not clean.startswith('---'):
                        # Se a linha for muito longa, trunca para não quebrar o índice
                        titulo_extra = f" - {clean[:50]}..." if len(clean) > 50 else f" - {clean}"
                        break
                
                processed_md_lines.append(f'## Página {num} <a id="{tid}"></a>\n\n')
                # Adiciona ao sumário: Página X - Título Encontrado
                toc_items.append(f'<li class="toc-page"><a href="#{tid}">Pág. {num}{titulo_extra}</a></li>')

            elif match_topico:
                titulo = match_topico.group(1).strip()
                tid = f"topico-{i}"
                processed_md_lines.append(f'### {titulo} <a id="{tid}"></a>\n\n')
                toc_items.append(f'<li class="toc-topic"><a href="#{tid}">{titulo}</a></li>')
            
            else:
                processed_md_lines.append(line)

        full_md = "".join(processed_md_lines)
        body_content = markdown.markdown(full_md, extensions=['extra'])

        with open(html_output_path, 'w', encoding='utf-8') as f:
            f.write(f"<!DOCTYPE html><html lang='pt-br'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>{self.STYLE}</head><body>")
            f.write("<div class='toc-box'><h2>📚 Índice do Livro</h2><ul class='toc-list'>")
            f.write("\n".join(toc_items))
            f.write("</ul></div>")
            f.write(body_content)
            f.write("</body></html>")
        
        print(f"Sucesso! Arquivo gerado com títulos no índice: '{html_output_path}'.")
