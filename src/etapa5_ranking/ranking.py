import os
import openpyxl

def normalize_status(status_str):
    """Normaliza e valida a string de status para 'ATIVO' ou 'BLOQUEADO'."""
    if not status_str:
        return "ATIVO"  # Padrão caso venha vazio
    
    status_clean = str(status_str).strip().upper()
    if status_clean in ["BLOQUEADO", "INATIVO", "BLOCKED"]:
        return "BLOQUEADO"
    return "ATIVO"

def normalize_inverse_value(value, min_val, max_val):
    """Normalizes values where lower is better (cost, lead time)."""
    if max_val == min_val:
        return 1.0
    return (max_val - value) / (max_val - min_val)

def normalize_direct_value(value, min_val, max_val):
    """Normalizes values where higher is better (capacity, quality)."""
    if max_val == min_val:
        return 1.0
    return (value - min_val) / (max_val - min_val)

def get_extrema(active_suppliers):
    """Returns min and max values considering only active suppliers."""
    if not active_suppliers:
        return None
        
    return {
        "custo": (min(s['custo'] for s in active_suppliers), max(s['custo'] for s in active_suppliers)),
        "prazo": (min(s['prazo_dias'] for s in active_suppliers), max(s['prazo_dias'] for s in active_suppliers)),
        "capacidade": (min(s['capacidade'] for s in active_suppliers), max(s['capacidade'] for s in active_suppliers)),
        "qualidade": (min(s['qualidade'] for s in active_suppliers), max(s['qualidade'] for s in active_suppliers)),
    }

def calculate_individual_score(supplier, weights, extrema):
    """Calculates the final score for a single supplier."""
    score = (
        normalize_inverse_value(supplier['custo'], *extrema['custo']) * weights['custo'] +
        normalize_inverse_value(supplier['prazo_dias'], *extrema['prazo']) * weights['prazo'] +
        normalize_direct_value(supplier['capacidade'], *extrema['capacidade']) * weights['capacidade'] +
        normalize_direct_value(supplier['qualidade'], *extrema['qualidade']) * weights['qualidade']
    )
    return score

def calculate_ranking(suppliers):
    """Calculates scores for active suppliers and leaves blocked ones as None."""
    weights = {
        "custo": 0.4,
        "prazo": 0.25,
        "capacidade": 0.2,
        "qualidade": 0.15
    }
    
    # Padroniza o status de todos os fornecedores
    for s in suppliers:
        s["status_normalizado"] = normalize_status(s.get("status"))
    
    # Filtra apenas os ativos para obter os limites min/max de cálculo
    active_suppliers = [s for s in suppliers if s["status_normalizado"] == "ATIVO"]
    extrema = get_extrema(active_suppliers)
    
    for s in suppliers:
        if s["status_normalizado"] == "BLOQUEADO":
            s["score"] = None  # Não calcula a nota para bloqueados
        else:
            s["score"] = calculate_individual_score(s, weights, extrema) if extrema else 0.0
            
    # Ordena: Ativos primeiro ordenados por Score (decrescente), depois Bloqueados
    return sorted(
        suppliers, 
        key=lambda x: (x["score"] is not None, x["score"] if x["score"] is not None else -1), 
        reverse=True
    )

def fill_spreadsheet(suppliers, filename="modelo_ranking.xlsx"):
    """Calcula o ranking e salva na planilha excel."""
    base_dir = os.path.dirname(__file__)
    relative_path = os.path.abspath(
        os.path.join(
            base_dir,
            "..",
            "..",
            "resources",
            "01_SELECAO_FORNECEDORES",
            filename,
        )
    )

    os.makedirs(os.path.dirname(relative_path), exist_ok=True)
    ranking = calculate_ranking(suppliers)

    if os.path.exists(relative_path):
        wb = openpyxl.load_workbook(relative_path)
        ws = wb.active
        ws.delete_rows(2, ws.max_row)
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Posicao", "Fornecedor", "Nota_Final", "Status", "Observacao"])

    for index, s in enumerate(ranking, 1):
        posicao = index
        fornecedor = s["fornecedor"]
        # Se for None grava nulo/vazio na planilha, se tiver score arredonda
        nota_final = round(s["score"], 4) if s["score"] is not None else None
        status = s["status_normalizado"]
        observacao = s.get("observacao", "")
        
        ws.append([posicao, fornecedor, nota_final, status, observacao])

    wb.save(relative_path)
    print(f"Planilha salva com sucesso em:\n{relative_path}")

if __name__ == "__main__":
    fornecedores_exemplo = [
        { 
            "fornecedor": "Fornecedor A", 
            "custo": 100, 
            "prazo_dias": 5, 
            "capacidade": 500, 
            "qualidade": 95,
            "status": "ativo", 
            "observacao": "Fornecedor ativo padrão"
        },
        { 
            "fornecedor": "Fornecedor B", 
            "custo": 80, 
            "prazo_dias": 2, 
            "capacidade": 600, 
            "qualidade": 90,
            "status": "BLOQUEADO", 
            "observacao": "Bloqueado por compliance"
        },
        { 
            "fornecedor": "Fornecedor C", 
            "custo": 120, 
            "prazo_dias": 3, 
            "capacidade": 300, 
            "qualidade": 98,
            "status": "Bloqueado",
            "observacao": "Problemas na entrega"
        }
    ]
    
    fill_spreadsheet(fornecedores_exemplo)