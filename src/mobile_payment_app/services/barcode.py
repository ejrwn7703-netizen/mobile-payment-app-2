"""바코드 스캔 및 상품 조회 서비스

바코드를 스캔하여 상품 정보를 조회하고 검증하는 서비스입니다.
"""
import re
from typing import Dict, Optional, List
import json
import os


# 샘플 상품 데이터베이스 (실제로는 DB에서 조회)
SAMPLE_PRODUCTS = {
    "8801234567890": {
        "barcode": "8801234567890",
        "name": "삼다수 2L",
        "price": 1500,
        "currency": "KRW",
        "category": "음료",
        "stock": 100,
        "weight": 2000,  # 그램
        "image_url": "/static/images/products/samdasoo.jpg"
    },
    "8809012345678": {
        "barcode": "8809012345678",
        "name": "신라면 5개입",
        "price": 4500,
        "currency": "KRW",
        "category": "식품",
        "stock": 50,
        "weight": 600,
        "image_url": "/static/images/products/shinramyun.jpg"
    },
    "8801099876543": {
        "barcode": "8801099876543",
        "name": "서울우유 1L",
        "price": 3200,
        "currency": "KRW",
        "category": "유제품",
        "stock": 30,
        "weight": 1000,
        "image_url": "/static/images/products/milk.jpg"
    },
    "8802345678901": {
        "barcode": "8802345678901",
        "name": "허니버터칩",
        "price": 2500,
        "currency": "KRW",
        "category": "과자",
        "stock": 75,
        "weight": 200,
        "image_url": "/static/images/products/chips.jpg"
    }
}


class BarcodeScanner:
    """바코드 스캔 및 상품 조회 서비스"""
    
    def __init__(self, products_db: Optional[Dict] = None):
        """
        Args:
            products_db: 상품 데이터베이스 (None이면 샘플 데이터 사용)
        """
        self.products_db = products_db or SAMPLE_PRODUCTS
    
    def validate_barcode(self, barcode: str) -> Dict[str, any]:
        """바코드 형식 검증
        
        Args:
            barcode: 검증할 바코드 문자열
            
        Returns:
            검증 결과 딕셔너리
        """
        # 바코드는 8-13자리 숫자여야 함
        if not barcode:
            return {
                "valid": False,
                "error": "EMPTY_BARCODE",
                "message": "바코드가 비어있습니다."
            }
        
        if not re.match(r'^[0-9]{8,13}$', barcode):
            return {
                "valid": False,
                "error": "INVALID_FORMAT",
                "message": "바코드 형식이 올바르지 않습니다. (8-13자리 숫자)"
            }
        
        return {"valid": True}
    
    def scan_product(self, barcode: str, store_id: Optional[str] = None) -> Dict[str, any]:
        """바코드를 스캔하여 상품 정보 조회
        
        Args:
            barcode: 스캔한 바코드
            store_id: 매장 ID (선택)
            
        Returns:
            상품 정보 또는 에러 정보
        """
        # 1. 바코드 형식 검증
        validation = self.validate_barcode(barcode)
        if not validation["valid"]:
            return {
                "success": False,
                "error_code": validation["error"],
                "message": validation["message"]
            }
        
        # 2. 상품 조회
        product = self.products_db.get(barcode)
        
        if not product:
            return {
                "success": False,
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "상품을 찾을 수 없습니다.",
                "barcode": barcode
            }
        
        # 3. 재고 확인
        if product.get("stock", 0) <= 0:
            return {
                "success": False,
                "error_code": "OUT_OF_STOCK",
                "message": "재고가 없는 상품입니다.",
                "product": product
            }
        
        # 4. 성공 응답
        return {
            "success": True,
            "product": product,
            "message": "상품을 찾았습니다."
        }
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """바코드로 상품 정보만 조회 (검증 없이)
        
        Args:
            barcode: 바코드
            
        Returns:
            상품 정보 또는 None
        """
        return self.products_db.get(barcode)
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """상품 검색 (이름으로)
        
        Args:
            query: 검색어
            limit: 최대 결과 수
            
        Returns:
            검색된 상품 목록
        """
        results = []
        query_lower = query.lower()
        
        for product in self.products_db.values():
            if query_lower in product["name"].lower():
                results.append(product)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_products(self) -> List[Dict]:
        """모든 상품 목록 조회
        
        Returns:
            전체 상품 목록
        """
        return list(self.products_db.values())
    
    def check_stock(self, barcode: str, quantity: int = 1) -> Dict[str, any]:
        """재고 확인
        
        Args:
            barcode: 바코드
            quantity: 필요한 수량
            
        Returns:
            재고 확인 결과
        """
        product = self.products_db.get(barcode)
        
        if not product:
            return {
                "available": False,
                "error": "PRODUCT_NOT_FOUND",
                "message": "상품을 찾을 수 없습니다."
            }
        
        current_stock = product.get("stock", 0)
        
        if current_stock < quantity:
            return {
                "available": False,
                "error": "INSUFFICIENT_STOCK",
                "message": f"재고가 부족합니다. (현재: {current_stock}, 필요: {quantity})",
                "current_stock": current_stock,
                "requested_quantity": quantity
            }
        
        return {
            "available": True,
            "current_stock": current_stock,
            "requested_quantity": quantity,
            "remaining_after_purchase": current_stock - quantity
        }


# 싱글톤 인스턴스
_scanner_instance = None

def get_barcode_scanner() -> BarcodeScanner:
    """바코드 스캐너 싱글톤 인스턴스 반환"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = BarcodeScanner()
    return _scanner_instance
