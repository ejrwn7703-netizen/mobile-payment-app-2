"""바코드 스캔 기능 테스트"""
import pytest
from src.mobile_payment_app.services.barcode import BarcodeScanner


class TestBarcodeScanner:
    def setup_method(self):
        self.scanner = BarcodeScanner()
    
    def test_validate_barcode_valid(self):
        """유효한 바코드 검증"""
        result = self.scanner.validate_barcode("8801234567890")
        assert result["valid"] is True
    
    def test_validate_barcode_empty(self):
        """빈 바코드 검증"""
        result = self.scanner.validate_barcode("")
        assert result["valid"] is False
        assert result["error"] == "EMPTY_BARCODE"
    
    def test_validate_barcode_invalid_format(self):
        """잘못된 형식의 바코드"""
        result = self.scanner.validate_barcode("abc123")
        assert result["valid"] is False
        assert result["error"] == "INVALID_FORMAT"
    
    def test_scan_product_success(self):
        """상품 스캔 성공"""
        result = self.scanner.scan_product("8801234567890")
        assert result["success"] is True
        assert "product" in result
        assert result["product"]["name"] == "삼다수 2L"
    
    def test_scan_product_not_found(self):
        """존재하지 않는 상품"""
        result = self.scanner.scan_product("9999999999999")
        assert result["success"] is False
        assert result["error_code"] == "PRODUCT_NOT_FOUND"
    
    def test_search_products(self):
        """상품 검색"""
        results = self.scanner.search_products("우유")
        assert len(results) > 0
        assert any("우유" in p["name"] for p in results)
    
    def test_check_stock_available(self):
        """재고 확인 - 재고 충분"""
        result = self.scanner.check_stock("8801234567890", 5)
        assert result["available"] is True
        assert result["current_stock"] >= 5
    
    def test_check_stock_insufficient(self):
        """재고 확인 - 재고 부족"""
        result = self.scanner.check_stock("8801234567890", 9999)
        assert result["available"] is False
        assert result["error"] == "INSUFFICIENT_STOCK"


class TestBarcodeScanAPI:
    """바코드 스캔 API 통합 테스트"""
    
    def test_scan_api_success(self, client):
        """스캔 API 성공"""
        response = client.post('/api/scan', json={
            'barcode': '8801234567890'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'product' in data
    
    def test_scan_api_missing_barcode(self, client):
        """스캔 API - 바코드 누락"""
        response = client.post('/api/scan', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_products_list_api(self, client):
        """상품 목록 조회 API"""
        response = client.get('/api/products')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['products']) > 0
    
    def test_products_search_api(self, client):
        """상품 검색 API"""
        response = client.get('/api/products?q=삼다수')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['query'] == '삼다수'
    
    def test_product_detail_api(self, client):
        """상품 상세 조회 API"""
        response = client.get('/api/products/8801234567890')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['product']['name'] == '삼다수 2L'
    
    def test_stock_check_api(self, client):
        """재고 확인 API"""
        response = client.get('/api/products/8801234567890/stock?quantity=5')
        assert response.status_code == 200
        data = response.get_json()
        assert data['available'] is True


@pytest.fixture
def client():
    """Flask 테스트 클라이언트"""
    from src.mobile_payment_app.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
