import re
import markdown

class GenericMarkdownEnhancer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.STYLE = """
            <style>
                :root { 
                    --bg: #ffffff; --text: #1f2328; --link: #0969da; 
                    --border: #d0d7de; --code-bg: #f6f8fa; --sidebar-bg: #f8f9fa;
                }
                @media (prefers-color-scheme: dark) {
                    :root { 
                        --bg: #0d1117; --text: #e6edf3; --link: #2f81f7; 
                        --border: #30363d; --code-bg: #161b22; --sidebar-bg: #010409;
                    }
                }
                
                body { 
                    display: grid; 
                    grid-template-columns: 300px 1fr; 
                    background: var(--bg); color: var(--text); 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                    margin: 0; 
                }

                .sidebar { 
                    height: 100vh; position: sticky; top: 0; 
                    background: var(--sidebar-bg); border-right: 1px solid var(--border);
                    padding: 20px; overflow-y: auto; 
                }

                .main-content { padding: 2rem 4rem; max-width: 850px; }
                .toc-list { list-style: none; padding-left: 0; }
                .toc-page { font-weight: bold; margin-top: 12px; font-size: 0.95em; border-bottom: 1px solid var(--border); padding-bottom: 5px; }
                .toc-topic { margin-left: 15px; font-size: 0.85em; list-style: none; border-left: 2px solid var(--border); padding-left: 10px; margin-top: 4px; }
                
                a { color: var(--link); text-decoration: none; }
                a:hover { text-decoration: underline; }

                .page-divider { 
                    border-top: 2px solid var(--border); margin: 50px 0 20px 0; padding-top: 10px;
                    color: #8b949e; font-size: 0.8em; text-transform: uppercase; font-weight: bold;
                }

                pre { background: var(--code-bg); padding: 1rem; border-radius: 8px; overflow-x: auto; border: 1px solid var(--border); }
                h1, h2, h3 { scroll-margin-top: 30px; }

                /* MELHORIA MOBILE: Sidebar vai para o topo em vez de sumir */
                @media (max-width: 768px) {
                    body { display: block; }
                    .sidebar { 
                        height: auto; position: relative; width: 100%; 
                        border-right: none; border-bottom: 2px solid var(--border);
                        padding: 10px; box-sizing: border-box;
                    }
                    .main-content { padding: 1.5rem; }
                    .toc-list { display: flex; flex-wrap: wrap; gap: 10px; }
                    .toc-page { border: 1px solid var(--border); padding: 5px 10px; border-radius: 4px; margin-top: 0; }
                    .toc-topic { display: none; } /* Esconde sub-tópicos no mobile para poupar espaço */
                }
            </style>
        """

    def process_and_view(self, html_output_path):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            processed_md_lines = []
            toc_items = [] 
            ultimo_titulo_registrado = "" 

            for i, line in enumerate(lines):
                # 1. Identifica Páginas
                match_pg = re.match(r'^## Página (\d+)', line)
                # 2. Identifica Títulos (H3)
                match_topico = re.match(r'^### (.*)', line)

                if match_pg:
                    num = match_pg.group(1)
                    tid = f"pg{num}"
                    processed_md_lines.append(f'<div class="page-divider" id="{tid}">Página {num}</div>\n\n')
                    toc_items.append(f'<li class="toc-page"><a href="#{tid}">Pág. {num}</a></li>')

                elif match_topico:
                    titulo_bruto = match_topico.group(1).strip()
                    titulo_lower = titulo_bruto.lower().replace(":", "").strip()
                    
                    # Termos que o LLM usa quando está "alucinando" um título
                    termos_proibidos = ["título do assunto", "assunto", "título", "revisão técnica"]
                    
                    # CRITÉRIO DE VALIDAÇÃO
                    # Se for um título real (não está na lista, não é repetido e tem tamanho bom)
                    if (titulo_bruto and 
                        titulo_lower not in termos_proibidos and 
                        titulo_lower != ultimo_titulo_registrado and 
                        len(titulo_lower) > 3):
                        
                        tid = f"topico-{i}"
                        processed_md_lines.append(f'### {titulo_bruto} <a id="{tid}"></a>\n\n')
                        toc_items.append(f'<li class="toc-topic"><a href="#{tid}">{titulo_bruto}</a></li>')
                        ultimo_titulo_registrado = titulo_lower
                    else:
                        # Se falhou na validação, NÃO DELETA. 
                        # Apenas remove os '###' e escreve como texto normal.
                        processed_md_lines.append(f"{titulo_bruto}\n\n")
                
                else:
                    # Linha de texto comum: mantém exatamente como está
                    processed_md_lines.append(line)

            # --- GERAÇÃO DO HTML ---
            full_md = "".join(processed_md_lines)
            body_content = markdown.markdown(full_md, extensions=['extra', 'codehilite'])

            with open(html_output_path, 'w', encoding='utf-8') as f:
                f.write(f"<!DOCTYPE html><html lang='pt-br'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>{self.STYLE}</head><body>")
                f.write("<aside class='sidebar'><h2>📚 Índice</h2><ul class='toc-list'>")
                f.write("\n".join(toc_items))
                f.write("</ul></aside>")
                f.write("<main class='main-content'>")
                f.write(body_content)
                f.write("</main></body></html>")
                
            print(f"✅ HTML gerado com sucesso em: {html_output_path}")

        except Exception as e:
            print(f"❌ Erro crítico no Enhancer: {e}")