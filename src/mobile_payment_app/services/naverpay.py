"""NaverPay gateway integration.

This module provides integration with NaverPay payment gateway.
Supports both sandbox and production modes.
"""
import uuid
import json
import os
import hashlib
import hmac
import time
import requests
from typing import Dict, Optional
from urllib.parse import urlencode

# File-based store path (can be customized via env var)
DEFAULT_STORE_PATH = os.environ.get("MOBILE_PAYMENTS_STORE", "data/payments.json")


def _ensure_store_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _load_store(path: str) -> Dict[str, Dict]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_store(path: str, store: Dict[str, Dict]):
    # atomic write
    _ensure_store_dir(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class NaverPayGateway:
    """NaverPay 결제 게이트웨이
    
    지원 모드:
    - mock: 로컬 개발용 Mock 구현
    - sandbox: 네이버페이 샌드박스 환경
    - production: 네이버페이 실제 결제 환경
    """
    
    SANDBOX_API_URL = "https://test-pay.naver.com/api"
    PRODUCTION_API_URL = "https://pay.naver.com/api"
    
    def __init__(self, client_id: str = None, client_secret: str = None, mode: str = "mock", store_path: str = None):
        self.client_id = client_id or os.environ.get("NAVER_PAY_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("NAVER_PAY_CLIENT_SECRET")
        self.mode = mode or os.environ.get("NAVER_PAY_MODE", "mock")
        self.store_path = store_path or DEFAULT_STORE_PATH
        
        # Mock 모드일 때만 로컬 저장소 사용
        if self.mode == "mock":
            self._store = _load_store(self.store_path)
        else:
            self._store = {}
            
        # API URL 설정
        if self.mode == "production":
            self.api_url = self.PRODUCTION_API_URL
        elif self.mode == "sandbox":
            self.api_url = self.SANDBOX_API_URL
        else:
            self.api_url = None  # Mock 모드
            
    def _persist(self):
        """Mock 모드에서만 파일에 저장"""
        if self.mode == "mock":
            _save_store(self.store_path, self._store)
    
    def _generate_signature(self, data: Dict) -> str:
        """네이버페이 API 서명 생성"""
        if not self.client_secret:
            raise ValueError("Client secret is required for signature generation")
            
        # 서명 대상 데이터를 정렬하여 문자열로 변환
        sorted_data = sorted(data.items())
        message = "&".join(f"{k}={v}" for k, v in sorted_data)
        
        # HMAC-SHA256 서명
        signature = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_api_request(self, endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
        """네이버페이 API 요청"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID and Secret are required for API requests")
            
        url = f"{self.api_url}/{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
                
            response.raise_for_status()
            return response.json()
            
        except ValueError as e:
            # JSON 파싱 에러
            return {
                "error": "INVALID_JSON_RESPONSE",
                "message": f"Invalid JSON response from API: {str(e)}",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # 네트워크 에러
            return {
                "error": "API_REQUEST_FAILED",
                "message": str(e),
                "success": False
            }
        except Exception as e:
            # 기타 에러
            return {
                "error": "UNKNOWN_ERROR",
                "message": str(e),
                "success": False
            }

    def process_payment(self, amount, currency, payment_method, order_id=None, return_url=None):
        """결제 요청 처리
        
        Mock 모드: 로컬 파일 기반 Mock 결제
        Sandbox/Production 모드: 실제 네이버페이 API 호출
        
        Returns a dict with keys: payment_id, redirect_url
        """
        if self.mode == "mock":
            return self._process_mock_payment(amount, currency, payment_method, order_id, return_url)
        else:
            return self._process_real_payment(amount, currency, payment_method, order_id, return_url)
    
    def _process_mock_payment(self, amount, currency, payment_method, order_id=None, return_url=None):
        """Mock 결제 처리 (기존 로직)"""
        payment_id = f"mock-{uuid.uuid4().hex}"
        token = uuid.uuid4().hex
        redirect_url = self._make_redirect_url(payment_id, token, return_url)

        self._store[payment_id] = {
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "method": payment_method,
            "order_id": order_id,
            "status": "created",
            "redirect_url": redirect_url,
            "token": token,
        }
        self._persist()

        return {"payment_id": payment_id, "redirect_url": redirect_url}
    
    def _process_real_payment(self, amount, currency, payment_method, order_id=None, return_url=None):
        """실제 네이버페이 API 결제 처리"""
        # 주문 ID 생성 (없으면)
        if not order_id:
            order_id = f"ORDER-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        
        # 네이버페이 결제 요청 데이터
        payment_data = {
            "merchantId": self.client_id,
            "merchantPayKey": order_id,
            "productName": "모바일 결제",
            "totalPayAmount": amount,
            "returnUrl": return_url or self._get_default_return_url(),
            "taxScopeAmount": amount,
            "taxExScopeAmount": 0,
            "productCount": 1,
        }
        
        # API 요청
        result = self._make_api_request("payment/reserve", method="POST", data=payment_data)
        
        if result.get("success") is False:
            # API 실패 시 에러 반환
            return {
                "error": result.get("error", "PAYMENT_FAILED"),
                "message": result.get("message", "결제 요청에 실패했습니다."),
                "success": False
            }
        
        # 성공 시 결제 ID와 redirect URL 반환
        payment_id = result.get("reserveId", order_id)
        redirect_url = result.get("paymentUrl") or f"{self.api_url}/payments/{payment_id}"
        
        # 로컬에도 저장 (추적용)
        self._store[payment_id] = {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "method": payment_method,
            "status": "reserved",
            "created_at": time.time(),
        }
        
        return {"payment_id": payment_id, "redirect_url": redirect_url}

    def get_payment_status(self, payment_id: str) -> Optional[str]:
        """결제 상태 조회"""
        if self.mode == "mock":
            # Mock 모드: 로컬 저장소에서 조회
            p = self._store.get(payment_id)
            if not p:
                return None
            return p.get("status")
        else:
            # 실제 API 모드: 네이버페이 API 호출
            return self._get_real_payment_status(payment_id)
    
    def _get_real_payment_status(self, payment_id: str) -> Optional[str]:
        """실제 네이버페이 API로 결제 상태 조회"""
        result = self._make_api_request(f"payment/{payment_id}", method="GET")
        
        if result.get("success") is False:
            return None
            
        # 네이버페이 상태 코드를 내부 상태로 변환
        naver_status = result.get("paymentStatus", "UNKNOWN")
        status_mapping = {
            "RESERVED": "reserved",
            "APPROVAL_REQUESTED": "pending",
            "APPROVED": "completed",
            "CANCELED": "cancelled",
            "FAILED": "failed",
        }
        
        return status_mapping.get(naver_status, "unknown")

    def handle_callback(self, payload: Dict) -> bool:
        """결제 콜백/웹훅 처리
        
        Mock 모드: 로컬 저장소 업데이트
        Sandbox/Production 모드: 네이버페이 콜백 검증 및 처리
        """
        if self.mode == "mock":
            return self._handle_mock_callback(payload)
        else:
            return self._handle_real_callback(payload)
    
    def _handle_mock_callback(self, payload: Dict) -> bool:
        """Mock 콜백 처리 (기존 로직)"""
        payment_id = payload.get("payment_id")
        status = payload.get("status")
        if not payment_id or not status:
            return False
        p = self._store.get(payment_id)
        if not p:
            return False
        p["status"] = status
        self._store[payment_id] = p
        self._persist()
        return True
    
    def _handle_real_callback(self, payload: Dict) -> bool:
        """실제 네이버페이 콜백 처리"""
        # 네이버페이 콜백 검증
        payment_id = payload.get("paymentId") or payload.get("payment_id")
        if not payment_id:
            return False
        
        # 서명 검증 (보안)
        if "signature" in payload:
            expected_signature = self._generate_signature({
                k: v for k, v in payload.items() if k != "signature"
            })
            if payload["signature"] != expected_signature:
                return False
        
        # 결제 상태 업데이트
        status = payload.get("paymentStatus", payload.get("status"))
        if payment_id in self._store:
            self._store[payment_id]["status"] = status
            self._store[payment_id]["updated_at"] = time.time()
        
        return True

    # testing helper
    def _dump_store(self):
        return self._store
    
    def _get_default_return_url(self) -> str:
        """기본 리턴 URL 가져오기"""
        base = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000").rstrip('/')
        return f"{base}/payments/complete"

    def _make_redirect_url(self, payment_id: str, token: str, return_url: str = None) -> str:
        """Construct redirect URL (Mock 모드용)

        Priority:
          1. explicit return_url (if provided)
          2. APP_BASE_URL environment variable
          3. default http://127.0.0.1:8000
        """
        if return_url:
            base = return_url.rstrip('/')
            # If return_url already contains query params, append with &
            sep = '&' if '?' in base else '?'
            return f"{base}{sep}payment_id={payment_id}&token={token}"

        return f"{self._get_default_return_url()}?payment_id={payment_id}&token={token}"
    
    def approve_payment(self, payment_id: str, **kwargs) -> Dict:
        """결제 승인 처리 (실제 API용)"""
        if self.mode == "mock":
            # Mock 모드: 자동 승인
            if payment_id in self._store:
                self._store[payment_id]["status"] = "completed"
                self._persist()
                return {"success": True, "payment_id": payment_id, "status": "completed"}
            return {"success": False, "error": "PAYMENT_NOT_FOUND"}
        else:
            # 실제 API: 네이버페이 승인 API 호출
            approval_data = {
                "paymentId": payment_id,
                **kwargs
            }
            result = self._make_api_request("payment/approve", method="POST", data=approval_data)
            return result
    
    def cancel_payment(self, payment_id: str, reason: str = None, amount: int = None) -> Dict:
        """결제 취소"""
        if self.mode == "mock":
            # Mock 모드: 상태만 변경
            if payment_id in self._store:
                self._store[payment_id]["status"] = "cancelled"
                self._store[payment_id]["cancel_reason"] = reason
                self._persist()
                return {"success": True, "payment_id": payment_id, "status": "cancelled"}
            return {"success": False, "error": "PAYMENT_NOT_FOUND"}
        else:
            # 실제 API: 네이버페이 취소 API 호출
            cancel_data = {
                "paymentId": payment_id,
                "cancelReason": reason or "사용자 요청",
            }
            if amount:
                cancel_data["cancelAmount"] = amount
            
            result = self._make_api_request("payment/cancel", method="POST", data=cancel_data)
            return result

