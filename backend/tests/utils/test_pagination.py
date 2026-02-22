"""
Testes para app/utils/pagination.py

Coverage target: 100%
Covers: validate_pagination, calculate_skip, paginate_response
"""
import pytest
from app.utils.pagination import (
    validate_pagination,
    calculate_skip,
    paginate_response
)
from app.config import MAX_PAGE_SIZE


class TestValidatePagination:
    """Testes para validate_pagination()"""
    
    def test_validate_pagination_valid_params(self):
        """Deve aceitar parâmetros válidos"""
        page, page_size = validate_pagination(1, 20)
        assert page == 1
        assert page_size == 20
    
    def test_validate_pagination_large_page_number(self):
        """Deve aceitar page grande (sem limite superior)"""
        page, page_size = validate_pagination(999, 50)
        assert page == 999
        assert page_size == 50
    
    def test_validate_pagination_page_less_than_one(self):
        """Deve rejeitar page < 1"""
        with pytest.raises(ValueError, match="page deve ser >= 1"):
            validate_pagination(0, 20)
        
        with pytest.raises(ValueError, match="page deve ser >= 1"):
            validate_pagination(-5, 20)
    
    def test_validate_pagination_page_size_less_than_one(self):
        """Deve rejeitar page_size < 1"""
        with pytest.raises(ValueError, match="page_size deve ser >= 1"):
            validate_pagination(1, 0)
        
        with pytest.raises(ValueError, match="page_size deve ser >= 1"):
            validate_pagination(1, -10)
    
    def test_validate_pagination_page_size_exceeds_max(self):
        """Deve limitar page_size ao MAX_PAGE_SIZE"""
        page, page_size = validate_pagination(1, 500)
        assert page == 1
        assert page_size == MAX_PAGE_SIZE  # 100
    
    def test_validate_pagination_page_size_at_max(self):
        """Deve aceitar page_size exatamente no limite"""
        page, page_size = validate_pagination(2, MAX_PAGE_SIZE)
        assert page == 2
        assert page_size == MAX_PAGE_SIZE


class TestCalculateSkip:
    """Testes para calculate_skip()"""
    
    def test_calculate_skip_first_page(self):
        """Primeira página deve ter skip=0"""
        skip = calculate_skip(page=1, page_size=20)
        assert skip == 0
    
    def test_calculate_skip_second_page(self):
        """Segunda página com page_size=20 deve ter skip=20"""
        skip = calculate_skip(page=2, page_size=20)
        assert skip == 20
    
    def test_calculate_skip_third_page(self):
        """Terceira página com page_size=10 deve ter skip=20"""
        skip = calculate_skip(page=3, page_size=10)
        assert skip == 20
    
    def test_calculate_skip_large_page(self):
        """Deve calcular corretamente para páginas grandes"""
        skip = calculate_skip(page=10, page_size=50)
        assert skip == 450
    
    def test_calculate_skip_page_size_one(self):
        """Deve funcionar com page_size=1"""
        skip = calculate_skip(page=5, page_size=1)
        assert skip == 4


class TestPaginateResponse:
    """Testes para paginate_response()"""
    
    def test_paginate_response_with_items(self):
        """Deve formatar resposta com itens corretamente"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = paginate_response(
            items=items,
            page=1,
            page_size=20,
            total=100
        )
        
        assert response == {
            "items": items,
            "page": 1,
            "page_size": 20,
            "total": 100
        }
    
    def test_paginate_response_empty_list(self):
        """Deve funcionar com lista vazia"""
        response = paginate_response(
            items=[],
            page=1,
            page_size=20,
            total=0
        )
        
        assert response == {
            "items": [],
            "page": 1,
            "page_size": 20,
            "total": 0
        }
    
    def test_paginate_response_last_page_partial(self):
        """Deve formatar última página parcial"""
        items = [{"id": 91}, {"id": 92}]  # últimos 2 de 92 total
        response = paginate_response(
            items=items,
            page=5,
            page_size=20,
            total=92
        )
        
        assert response["items"] == items
        assert response["page"] == 5
        assert response["page_size"] == 20
        assert response["total"] == 92
    
    def test_paginate_response_preserves_data_types(self):
        """Deve preservar tipos de dados nos itens"""
        items = [
            {"id": 1, "name": "Test", "value": 123.45, "active": True},
            {"id": 2, "name": None, "value": 0, "active": False}
        ]
        response = paginate_response(
            items=items,
            page=1,
            page_size=10,
            total=2
        )
        
        assert response["items"] == items
        # Verificar que tipos foram preservados
        assert isinstance(response["items"][0]["value"], float)
        assert isinstance(response["items"][0]["active"], bool)
        assert response["items"][1]["name"] is None


class TestPaginationIntegration:
    """Testes de integração entre funções de paginação"""
    
    def test_full_pagination_flow(self):
        """Deve funcionar todo o fluxo de paginação"""
        # Validar parâmetros
        page, page_size = validate_pagination(2, 25)
        
        # Calcular skip
        skip = calculate_skip(page, page_size)
        assert skip == 25
        
        # Simular query (fake data)
        fake_items = [{"id": i} for i in range(26, 51)]  # items 26-50
        
        # Formatar resposta
        response = paginate_response(
            items=fake_items,
            page=page,
            page_size=page_size,
            total=100
        )
        
        assert response["page"] == 2
        assert response["page_size"] == 25
        assert len(response["items"]) == 25
        assert response["total"] == 100
    
    def test_pagination_edge_case_page_beyond_total(self):
        """Deve permitir page além do total (retorna vazio)"""
        page, page_size = validate_pagination(10, 20)
        skip = calculate_skip(page, page_size)
        
        # Simulando query que retorna vazio (página além do total)
        response = paginate_response(
            items=[],
            page=page,
            page_size=page_size,
            total=50  # só 50 items, mas pedindo page 10
        )
        
        assert response["items"] == []
        assert response["page"] == 10
        assert response["total"] == 50
