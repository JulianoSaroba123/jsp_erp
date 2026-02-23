#!/usr/bin/env python3
"""
Smoke Test - ERP JSP Staging/Production
=========================================
Valida serviço pós-deploy com testes end-to-end.

Usage:
    # Local
    STAGING_BASE_URL=http://127.0.0.1:8000 python scripts/smoke_test_staging.py
    
    # Staging/Produção
    STAGING_BASE_URL=https://jsp-erp-backend.onrender.com python scripts/smoke_test_staging.py

Exit codes:
    0 - All tests passed
    1 - One or more tests failed
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# =============================================================================
# Configuration
# =============================================================================

BASE_URL = os.getenv("STAGING_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = 10  # seconds
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"

# Test user credentials (criado dinamicamente no teste)
TEST_EMAIL = f"smoketest_{int(time.time())}@example.com"
TEST_PASSWORD = "SmokeTest123!Strong"
TEST_NAME = "Smoke Test User"

# =============================================================================
# Utilities
# =============================================================================

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, color: str = ""):
    """Log message with optional color"""
    print(f"{color}{message}{Colors.RESET}")

def log_test(name: str):
    """Log test start"""
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}TEST: {name}{Colors.RESET}")
    print(f"{'='*60}")

def log_success(message: str):
    """Log success"""
    log(f"✅ {message}", Colors.GREEN)

def log_error(message: str):
    """Log error"""
    log(f"❌ {message}", Colors.RED)

def log_warning(message: str):
    """Log warning"""
    log(f"⚠️  {message}", Colors.YELLOW)

def log_info(message: str):
    """Log info"""
    log(f"ℹ️  {message}", Colors.BLUE)

def log_json(data: dict):
    """Pretty print JSON"""
    if VERBOSE:
        print(json.dumps(data, indent=2))

# =============================================================================
# Test Functions
# =============================================================================

def test_health() -> bool:
    """Test 1: GET /health - Service is alive"""
    log_test("Health Check")
    
    try:
        log_info(f"GET {BASE_URL}/health")
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        
        log_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            log_error(f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        log_json(data)
        
        # Validate required fields
        required_fields = ["ok", "service", "env"]
        for field in required_fields:
            if field not in data:
                log_error(f"Missing required field: {field}")
                return False
        
        # Validate values
        if data.get("ok") is not True:
            log_error(f"Database unhealthy: ok={data.get('ok')}")
            log_error(f"Database status: {data.get('database')}")
            return False
        
        if data.get("service") != "jsp_erp":
            log_error(f"Wrong service: {data.get('service')}")
            return False
        
        if data.get("env") not in ["development", "production", "test"]:
            log_error(f"Invalid environment: {data.get('env')}")
            return False
        
        log_success(f"Health check OK - env={data.get('env')}, db={data.get('database')}")
        return True
        
    except requests.exceptions.Timeout:
        log_error(f"Timeout after {TIMEOUT}s")
        return False
    except requests.exceptions.ConnectionError:
        log_error(f"Cannot connect to {BASE_URL}")
        log_warning("Make sure service is running")
        return False
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        return False


def test_register_user() -> Tuple[bool, Optional[str]]:
    """Test 2: POST /auth/register - Create test user"""
    log_test("User Registration")
    
    try:
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        }
        
        log_info(f"POST {BASE_URL}/auth/register")
        log_info(f"Email: {TEST_EMAIL}")
        
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=payload,
            timeout=TIMEOUT
        )
        
        log_info(f"Status: {response.status_code}")
        
        if response.status_code != 201:
            log_error(f"Expected 201, got {response.status_code}")
            if response.status_code == 400:
                data = response.json()
                log_error(f"Detail: {data.get('detail')}")
            return False, None
        
        data = response.json()
        log_json(data)
        
        user_id = data.get("id")
        if not user_id:
            log_error("No user ID in response")
            return False, None
        
        log_success(f"User created: {user_id}")
        return True, user_id
        
    except Exception as e:
        log_error(f"Registration failed: {str(e)}")
        return False, None


def test_login() -> Tuple[bool, Optional[str]]:
    """Test 3: POST /auth/login - Get access token"""
    log_test("User Login")
    
    try:
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        log_info(f"POST {BASE_URL}/auth/login")
        log_info(f"Email: {TEST_EMAIL}")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload,
            timeout=TIMEOUT
        )
        
        log_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            log_error(f"Expected 200, got {response.status_code}")
            data = response.json()
            log_error(f"Detail: {data.get('detail')}")
            return False, None
        
        data = response.json()
        log_json(data)
        
        token = data.get("access_token")
        if not token:
            log_error("No access_token in response")
            return False, None
        
        token_type = data.get("token_type")
        if token_type != "bearer":
            log_error(f"Invalid token_type: {token_type}")
            return False, None
        
        log_success(f"Login successful - token: {token[:20]}...")
        return True, token
        
    except Exception as e:
        log_error(f"Login failed: {str(e)}")
        return False, None


def test_authenticated_endpoint(token: str) -> bool:
    """Test 4: GET /users/me - Validate authentication"""
    log_test("Authenticated Endpoint")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        log_info(f"GET {BASE_URL}/users/me")
        log_info(f"Token: {token[:20]}...")
        
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers=headers,
            timeout=TIMEOUT
        )
        
        log_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            log_error(f"Expected 200, got {response.status_code}")
            data = response.json()
            log_error(f"Detail: {data.get('detail')}")
            return False
        
        data = response.json()
        log_json(data)
        
        if data.get("email") != TEST_EMAIL:
            log_error(f"Email mismatch: {data.get('email')} != {TEST_EMAIL}")
            return False
        
        log_success(f"Authentication OK - user: {data.get('full_name')}")
        return True
        
    except Exception as e:
        log_error(f"Auth endpoint failed: {str(e)}")
        return False


def test_list_orders(token: str) -> bool:
    """Test 5: GET /orders - List orders (empty or with data)"""
    log_test("List Orders (Protected)")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        log_info(f"GET {BASE_URL}/orders")
        
        response = requests.get(
            f"{BASE_URL}/orders",
            headers=headers,
            timeout=TIMEOUT
        )
        
        log_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            log_error(f"Expected 200, got {response.status_code}")
            data = response.json()
            log_error(f"Detail: {data.get('detail')}")
            return False
        
        data = response.json()
        log_json(data)
        
        # Validate response structure (paginated)
        if "items" not in data or "total" not in data:
            log_error("Invalid response structure (missing 'items' or 'total')")
            return False
        
        order_count = len(data.get("items", []))
        total_count = data.get("total", 0)
        
        log_success(f"Orders list OK - showing {order_count} of {total_count} total")
        return True
        
    except Exception as e:
        log_error(f"List orders failed: {str(e)}")
        return False


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    """Run all smoke tests"""
    start_time = time.time()
    
    print("\n" + "="*60)
    print(f"{Colors.BOLD}🧪 SMOKE TEST - ERP JSP{Colors.RESET}")
    print("="*60)
    log_info(f"Target: {BASE_URL}")
    log_info(f"Time: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {
        "health": False,
        "register": False,
        "login": False,
        "auth_endpoint": False,
        "list_orders": False
    }
    
    token = None
    user_id = None
    
    # Test 1: Health
    results["health"] = test_health()
    if not results["health"]:
        log_error("Health check failed - stopping tests")
        return 1
    
    # Test 2: Register
    results["register"], user_id = test_register_user()
    if not results["register"]:
        log_warning("Registration failed - trying to login with existing user")
        # Continue to login test (user might already exist)
    
    # Test 3: Login
    results["login"], token = test_login()
    if not results["login"]:
        log_error("Login failed - cannot test protected endpoints")
        # Skip remaining tests
    else:
        # Test 4: Authenticated endpoint
        results["auth_endpoint"] = test_authenticated_endpoint(token)
        
        # Test 5: List orders
        results["list_orders"] = test_list_orders(token)
    
    # Summary
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print(f"{Colors.BOLD}📊 TEST SUMMARY{Colors.RESET}")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed_test else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{test_name:20s} {status}")
    
    print("="*60)
    
    if passed == total:
        log_success(f"ALL TESTS PASSED ({passed}/{total})")
        log_info(f"Time: {elapsed:.2f}s")
        print("="*60)
        print(f"\n{Colors.GREEN}🎉 Staging is READY!{Colors.RESET}\n")
        return 0
    else:
        log_error(f"SOME TESTS FAILED ({passed}/{total})")
        log_info(f"Time: {elapsed:.2f}s")
        print("="*60)
        print(f"\n{Colors.RED}❌ Staging has issues - check logs above{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
