#!/usr/bin/env python3
"""
Quick test script para validar health endpoint localmente
Usage: python test_health_local.py
"""
import requests
import json
import sys

def test_health_endpoint(base_url="http://127.0.0.1:8000"):
    """Testa o endpoint /health e valida formato staging-ready"""
    print(f"🔍 Testing health endpoint: {base_url}/health\n")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        print(f"\nResponse JSON:")
        print(json.dumps(data, indent=2))
        
        # Validar campos obrigatórios
        required_fields = ["ok", "service", "env"]
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            print(f"\n❌ FAILED: Missing required fields: {missing}")
            return False
        
        # Validar valores específicos
        checks = []
        
        if data.get("ok") is True:
            checks.append("✅ ok: true - Database healthy")
        else:
            checks.append(f"⚠️  ok: {data.get('ok')} - Check database connection")
        
        if data.get("service") == "jsp_erp":
            checks.append("✅ service: jsp_erp")
        else:
            checks.append(f"❌ service: {data.get('service')} (expected 'jsp_erp')")
        
        if data.get("env") in ["development", "test", "production"]:
            checks.append(f"✅ env: {data.get('env')}")
        else:
            checks.append(f"❌ env: {data.get('env')} (invalid)")
        
        # Campos legados (backward compatibility)
        if "app" in data and "version" in data and "database" in data:
            checks.append("✅ Legacy fields present (backward compatible)")
        else:
            checks.append("⚠️  Some legacy fields missing")
        
        print("\nValidation Results:")
        for check in checks:
            print(f"  {check}")
        
        # Verifica se todos os checks passaram
        failed = [c for c in checks if c.startswith("❌")]
        if failed:
            print("\n❌ VALIDATION FAILED")
            return False
        
        print("\n✅ ALL CHECKS PASSED - Staging ready!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED: Could not connect to {base_url}")
        print("   Make sure the server is running:")
        print("   cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return False
    
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


if __name__ == "__main__":
    # Permite passar URL custom via argumento
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    success = test_health_endpoint(url)
    sys.exit(0 if success else 1)
