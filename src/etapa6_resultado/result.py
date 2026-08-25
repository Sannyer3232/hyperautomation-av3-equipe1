import os
import openpyxl
from jinja2 import Environment, FileSystemLoader

def load_ranking_data(filename="modelo_ranking.xlsx"):
    """Reads ranking data from the Excel spreadsheet."""
    base_dir = os.path.dirname(__file__)
    excel_path = os.path.abspath(
        os.path.join(base_dir, "..", "..", "resources", "01_SELECAO_FORNECEDORES", filename)
    )

    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {excel_path}")

    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    
    data = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(cell is None for cell in row):
            continue
            
        status_val = str(row[3]).strip() if row[3] is not None else "Pendente"
        is_blocked = status_val.upper() in ["BLOQUEADO", "INATIVO", "BLOCKED"]
        
        # Se estiver bloqueado ou a nota for Nula/None, atribui "-"
        if is_blocked or row[2] is None:
            nota_final = "-"
        else:
            nota_final = row[2]

        data.append({
            "posicao": row[0] if row[0] is not None else "-",
            "fornecedor": str(row[1]) if row[1] is not None else "Sem Nome",
            "nota_final": nota_final,
            "status": status_val,
            "observacao": str(row[4]) if row[4] is not None else "Sem observações"
        })
    return data

def generate_html_report(data, template_name="template_result.html", output_file="doc/relatorio_ranking.html"):
    """Generates an HTML report loading the template from an external file."""
    base_dir = os.path.dirname(__file__)
    
    env = Environment(loader=FileSystemLoader(base_dir))
    template = env.get_template(template_name)
    
    total_suppliers = len(data)
    
    # Contagens de status
    approved_count = sum(1 for item in data if str(item["status"]).strip().upper() == "ATIVO")
    blocked_count = sum(1 for item in data if str(item["status"]).strip().upper() in ["BLOQUEADO", "INATIVO", "BLOCKED"])
    
    # Filtra apenas os ativos para encontrar o melhor fornecedor
    active_suppliers = [item for item in data if str(item["status"]).strip().upper() == "ATIVO"]
    
    best_supplier = None
    if active_suppliers:
        best_supplier = min(
            active_suppliers, 
            key=lambda x: x["posicao"] if isinstance(x["posicao"], (int, float)) else float('inf')
        )

    html_content = template.render(
        data=data, 
        total_suppliers=total_suppliers, 
        approved_count=approved_count, 
        blocked_count=blocked_count,
        best_supplier=best_supplier
    )
    
    output_path = os.path.join(base_dir, output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Relatório gerado com sucesso em: {output_path}")

if __name__ == "__main__":
    try:
        suppliers_data = load_ranking_data()
        generate_html_report(suppliers_data)
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")