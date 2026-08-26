from ranking import (
    normalize_status,
    normalize_inverse_value,
    normalize_direct_value,
    get_extrema,
    calculate_ranking
)

def test_normalize_status():
    assert normalize_status("ativo") == "ATIVO"
    assert normalize_status(" BLOQUEADO ") == "BLOQUEADO"
    assert normalize_status("inativo") == "BLOQUEADO"
    assert normalize_status("blocked") == "BLOQUEADO"
    assert normalize_status(None) == "ATIVO"

def test_normalize_inverse_value():
    assert normalize_inverse_value(100, 100, 200) == 1.0  # Menor valor = 1.0
    assert normalize_inverse_value(200, 100, 200) == 0.0  # Maior valor = 0.0
    assert normalize_inverse_value(150, 100, 200) == 0.5  # Valor meio = 0.5
    assert normalize_inverse_value(100, 100, 100) == 1.0  # Trata min == max

def test_normalize_direct_value():
    assert normalize_direct_value(200, 100, 200) == 1.0  # Maior valor = 1.0
    assert normalize_direct_value(100, 100, 200) == 0.0  # Menor valor = 0.0
    assert normalize_direct_value(150, 100, 200) == 0.5  # Valor meio = 0.5
    assert normalize_direct_value(100, 100, 100) == 1.0  # Trata min == max

def test_get_extrema():
    suppliers = [
        {"custo": 100, "prazo_dias": 5, "capacidade": 500, "qualidade": 95},
        {"custo": 120, "prazo_dias": 3, "capacidade": 300, "qualidade": 98}
    ]
    extrema = get_extrema(suppliers)
    assert extrema["custo"] == (100, 120)
    assert extrema["prazo"] == (3, 5)
    assert extrema["capacidade"] == (300, 500)
    assert extrema["qualidade"] == (95, 98)

def test_calculate_ranking_com_bloqueados():
    suppliers = [
        {"fornecedor": "A", "custo": 100, "prazo_dias": 5, "capacidade": 500, "qualidade": 95, "status": "ativo"},
        {"fornecedor": "B", "custo": 80, "prazo_dias": 2, "capacidade": 600, "qualidade": 90, "status": "BLOQUEADO"},
        {"fornecedor": "C", "custo": 120, "prazo_dias": 3, "capacidade": 300, "qualidade": 98, "status": "ativo"}
    ]
    
    ranking = calculate_ranking(suppliers)
    
    assert len(ranking) == 3
    
    # Ativos devem vir primeiro no ranking
    assert ranking[0]["status_normalizado"] == "ATIVO"
    assert ranking[1]["status_normalizado"] == "ATIVO"
    assert ranking[2]["status_normalizado"] == "BLOQUEADO"
    
    # Bloqueados devem ter score None
    assert ranking[2]["score"] is None
    
    # Verifica se a ordenação dos ativos foi feita (decrescente)
    assert ranking[0]["score"] >= ranking[1]["score"]