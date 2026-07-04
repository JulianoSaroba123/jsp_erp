"""
External APIs para consulta de CNPJ e CEP
Integrações com ReceitaWS (CNPJ) e ViaCEP (endereço)
"""
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class ExternalAPIError(Exception):
    """Erro customizado para APIs externas"""
    pass


# ==================== CNPJ - ReceitaWS ====================

class ReceitaWSService:
    """
    Serviço para consulta de CNPJ na ReceitaWS.
    API pública do governo brasileiro com dados de empresas.
    """
    
    BASE_URL = "https://www.receitaws.com.br/v1/cnpj"
    TIMEOUT = 15.0  # 15 segundos de timeout
    
    @staticmethod
    def limpar_cnpj(cnpj: str) -> str:
        """Remove formatação do CNPJ (mantém apenas dígitos)"""
        return ''.join(filter(str.isdigit, cnpj))
    
    @staticmethod
    async def consultar_cnpj(cnpj: str) -> Dict[str, Any]:
        """
        Consulta dados de uma empresa pelo CNPJ.
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            Dicionário com dados da empresa:
            {
                "nome": "Razão Social",
                "nome_fantasia": "Nome Fantasia",
                "cnpj": "12345678000190",
                "email": "contato@empresa.com.br",
                "telefone": "(11) 1234-5678",
                "situacao": "ATIVA",
                "cep": "01310-100",
                "logradouro": "Avenida Paulista",
                "numero": "1578",
                "complemento": "Andar 5",
                "bairro": "Bela Vista",
                "municipio": "São Paulo",
                "uf": "SP"
            }
            
        Raises:
            HTTPException: Se CNPJ inválido ou não encontrado
        """
        try:
            cnpj_limpo = ReceitaWSService.limpar_cnpj(cnpj)
            
            # Validação básica
            if len(cnpj_limpo) != 14:
                raise HTTPException(
                    status_code=400,
                    detail="CNPJ deve ter 14 dígitos"
                )
            
            # Faz requisição assíncrona
            url = f"{ReceitaWSService.BASE_URL}/{cnpj_limpo}"
            logger.info(f"Consultando CNPJ {cnpj_limpo} em {url}")
            
            async with httpx.AsyncClient(timeout=ReceitaWSService.TIMEOUT) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verifica se houve erro na resposta da API
                    if data.get('status') == 'ERROR':
                        raise HTTPException(
                            status_code=404,
                            detail=data.get('message', 'CNPJ não encontrado')
                        )
                    
                    # Normaliza resposta
                    return {
                        "nome": data.get("nome", ""),
                        "nome_fantasia": data.get("fantasia", ""),
                        "cnpj": data.get("cnpj", cnpj_limpo),
                        "email": data.get("email", ""),
                        "telefone": data.get("telefone", ""),
                        "situacao": data.get("situacao", ""),
                        "data_abertura": data.get("abertura", ""),
                        "porte": data.get("porte", ""),
                        "natureza_juridica": data.get("natureza_juridica", ""),
                        # Endereço
                        "cep": data.get("cep", ""),
                        "logradouro": data.get("logradouro", ""),
                        "numero": data.get("numero", ""),
                        "complemento": data.get("complemento", ""),
                        "bairro": data.get("bairro", ""),
                        "municipio": data.get("municipio", ""),
                        "uf": data.get("uf", "")
                    }
                
                elif response.status_code == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit excedido para CNPJ {cnpj_limpo}")
                    raise HTTPException(
                        status_code=429,
                        detail="Muitas requisições. Aguarde alguns minutos e tente novamente."
                    )
                
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Erro ao consultar API ReceitaWS"
                    )
        
        except httpx.TimeoutException:
            logger.error(f"Timeout ao consultar CNPJ {cnpj}")
            raise HTTPException(
                status_code=504,
                detail="Timeout ao consultar CNPJ. Tente novamente."
            )
        
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão ao consultar CNPJ: {e}")
            raise HTTPException(
                status_code=503,
                detail="Erro ao conectar com o serviço de consulta de CNPJ"
            )
        
        except HTTPException:
            # Re-raise HTTPException já tratadas
            raise
        
        except Exception as e:
            logger.error(f"Erro inesperado ao consultar CNPJ: {e}")
            raise HTTPException(
                status_code=500,
                detail="Erro interno ao consultar CNPJ"
            )


# ==================== CEP - ViaCEP ====================

class ViaCEPService:
    """
    Serviço para consulta de CEP no ViaCEP.
    API pública dos Correios com dados de endereços brasileiros.
    """
    
    BASE_URL = "https://viacep.com.br/ws"
    TIMEOUT = 10.0  # 10 segundos de timeout
    
    @staticmethod
    def limpar_cep(cep: str) -> str:
        """Remove formatação do CEP (mantém apenas dígitos)"""
        return ''.join(filter(str.isdigit, cep))
    
    @staticmethod
    async def consultar_cep(cep: str) -> Dict[str, Any]:
        """
        Consulta endereço pelo CEP.
        
        Args:
            cep: CEP com ou sem formatação (ex: "01310-100" ou "01310100")
            
        Returns:
            Dicionário com dados do endereço:
            {
                "cep": "01310-100",
                "logradouro": "Avenida Paulista",
                "complemento": "de 612 a 1510 - lado par",
                "bairro": "Bela Vista",
                "localidade": "São Paulo",
                "uf": "SP",
                "cidade": "São Paulo"
            }
            
        Raises:
            HTTPException: Se CEP inválido ou não encontrado
        """
        try:
            cep_limpo = ViaCEPService.limpar_cep(cep)
            
            # Validação básica
            if len(cep_limpo) != 8:
                raise HTTPException(
                    status_code=400,
                    detail="CEP deve ter 8 dígitos"
                )
            
            # Faz requisição assíncrona
            url = f"{ViaCEPService.BASE_URL}/{cep_limpo}/json/"
            logger.info(f"Consultando CEP {cep_limpo} em {url}")
            
            async with httpx.AsyncClient(timeout=ViaCEPService.TIMEOUT) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # ViaCEP retorna {"erro": true} se CEP não encontrado
                    if data.get('erro'):
                        raise HTTPException(
                            status_code=404,
                            detail="CEP não encontrado"
                        )
                    
                    # Normaliza resposta
                    return {
                        "cep": data.get("cep", ""),
                        "logradouro": data.get("logradouro", ""),
                        "complemento": data.get("complemento", ""),
                        "bairro": data.get("bairro", ""),
                        "localidade": data.get("localidade", ""),
                        "cidade": data.get("localidade", ""),  # Alias para cidade
                        "uf": data.get("uf", ""),
                        "ibge": data.get("ibge", ""),
                        "gia": data.get("gia", ""),
                        "ddd": data.get("ddd", ""),
                        "siafi": data.get("siafi", "")
                    }
                
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Erro ao consultar API ViaCEP"
                    )
        
        except httpx.TimeoutException:
            logger.error(f"Timeout ao consultar CEP {cep}")
            raise HTTPException(
                status_code=504,
                detail="Timeout ao consultar CEP. Tente novamente."
            )
        
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão ao consultar CEP: {e}")
            raise HTTPException(
                status_code=503,
                detail="Erro ao conectar com o serviço de consulta de CEP"
            )
        
        except HTTPException:
            # Re-raise HTTPException já tratadas
            raise
        
        except Exception as e:
            logger.error(f"Erro inesperado ao consultar CEP: {e}")
            raise HTTPException(
                status_code=500,
                detail="Erro interno ao consultar CEP"
            )


# ==================== FUNÇÕES DE CONVENIÊNCIA ====================

async def consultar_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    """
    Wrapper simplificado para consulta de CNPJ.
    Retorna None se não encontrado ao invés de levantar exceção.
    """
    try:
        return await ReceitaWSService.consultar_cnpj(cnpj)
    except HTTPException as e:
        if e.status_code == 404:
            return None
        raise


async def consultar_cep(cep: str) -> Optional[Dict[str, Any]]:
    """
    Wrapper simplificado para consulta de CEP.
    Retorna None se não encontrado ao invés de levantar exceção.
    """
    try:
        return await ViaCEPService.consultar_cep(cep)
    except HTTPException as e:
        if e.status_code == 404:
            return None
        raise
