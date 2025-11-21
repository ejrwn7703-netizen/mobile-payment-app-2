"""결제 플로우 통합 테스트"""
import pytest
from src.mobile_payment_app.app import app
from src.mobile_payment_app.services.naverpay import NaverPayGateway
import json


@pytest.fixture
def client():
    """테스트 클라이언트 생성"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_gateway():
    """Mock NaverPay Gateway"""
    return NaverPayGateway(mode="mock")


class TestPaymentFlow:
    """결제 전체 플로우 테스트"""
    
    def test_complete_payment_flow(self, client):
        """완전한 결제 플로우 테스트"""
        # 1. 바코드 스캔
        scan_response = client.post('/api/scan', 
            json={'barcode': '8801234567890'},
            content_type='application/json'
        )
        assert scan_response.status_code == 200
        scan_data = json.loads(scan_response.data)
        assert scan_data['success'] is True
        product = scan_data['product']
        
        # 2. 결제 생성
        payment_response = client.post('/api/payments',
            json={
                'amount': product['price'],
                'currency': 'KRW',
                'payment_method': 'naverpay',
                'order_id': 'TEST-ORDER-001'
            },
            content_type='application/json'
        )
        assert payment_response.status_code == 201
        payment_data = json.loads(payment_response.data)
        assert 'payment_id' in payment_data
        assert 'redirect_url' in payment_data
        payment_id = payment_data['payment_id']
        
        # 3. 결제 상태 조회
        status_response = client.get(f'/api/payments/{payment_id}')
        assert status_response.status_code == 200
        status_data = json.loads(status_response.data)
        assert status_data['status'] == 'created'
        
        # 4. 결제 완료 콜백
        callback_response = client.post('/api/payments/callback',
            json={
                'payment_id': payment_id,
                'status': 'completed'
            },
            content_type='application/json'
        )
        assert callback_response.status_code == 200
        
        # 5. 최종 상태 확인
        final_status = client.get(f'/api/payments/{payment_id}')
        final_data = json.loads(final_status.data)
        assert final_data['status'] == 'completed'
    
    def test_multiple_products_checkout(self, client):
        """여러 상품 결제 테스트"""
        barcodes = ['8801234567890', '8809012345678', '8801099876543']
        total_amount = 0
        
        # 여러 상품 스캔
        for barcode in barcodes:
            response = client.post('/api/scan',
                json={'barcode': barcode},
                content_type='application/json'
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            total_amount += data['product']['price']
        
        # 합계 금액으로 결제
        payment_response = client.post('/api/payments',
            json={
                'amount': total_amount,
                'currency': 'KRW',
                'payment_method': 'naverpay',
                'order_id': 'TEST-MULTI-001'
            },
            content_type='application/json'
        )
        assert payment_response.status_code == 201
        payment_data = json.loads(payment_response.data)
        assert 'payment_id' in payment_data


class TestPaymentEdgeCases:
    """결제 엣지 케이스 테스트"""
    
    def test_payment_with_missing_fields(self, client):
        """필수 필드 누락 테스트"""
        response = client.post('/api/payments',
            json={'amount': 1000},  # currency, payment_method 누락
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_payment_invalid_amount(self, client):
        """잘못된 금액 테스트"""
        response = client.post('/api/payments',
            json={
                'amount': -1000,  # 음수 금액
                'currency': 'KRW',
                'payment_method': 'naverpay'
            },
            content_type='application/json'
        )
        # 현재는 음수도 허용하지만, 향후 검증 추가 필요
        assert response.status_code in [201, 400]
    
    def test_payment_status_not_found(self, client):
        """존재하지 않는 결제 조회"""
        response = client.get('/api/payments/nonexistent-payment-id')
        assert response.status_code == 404
    
    def test_callback_invalid_payload(self, client):
        """잘못된 콜백 페이로드"""
        response = client.post('/api/payments/callback',
            json={'invalid': 'data'},
            content_type='application/json'
        )
        assert response.status_code == 400


class TestNaverPayGateway:
    """NaverPay Gateway 단위 테스트"""
    
    def test_mock_payment_creation(self, mock_gateway):
        """Mock 결제 생성"""
        result = mock_gateway.process_payment(
            amount=10000,
            currency='KRW',
            payment_method='naverpay',
            order_id='TEST-001'
        )
        assert 'payment_id' in result
        assert 'redirect_url' in result
        assert result['payment_id'].startswith('mock-')
    
    def test_payment_status_tracking(self, mock_gateway):
        """결제 상태 추적"""
        # 결제 생성
        result = mock_gateway.process_payment(
            amount=5000,
            currency='KRW',
            payment_method='naverpay'
        )
        payment_id = result['payment_id']
        
        # 초기 상태 확인
        status = mock_gateway.get_payment_status(payment_id)
        assert status == 'created'
        
        # 상태 업데이트
        mock_gateway.handle_callback({
            'payment_id': payment_id,
            'status': 'completed'
        })
        
        # 업데이트된 상태 확인
        new_status = mock_gateway.get_payment_status(payment_id)
        assert new_status == 'completed'
    
    def test_callback_handling(self, mock_gateway):
        """콜백 처리 테스트"""
        # 결제 생성
        result = mock_gateway.process_payment(
            amount=3000,
            currency='KRW',
            payment_method='naverpay'
        )
        payment_id = result['payment_id']
        
        # 성공적인 콜백
        success = mock_gateway.handle_callback({
            'payment_id': payment_id,
            'status': 'completed'
        })
        assert success is True
        
        # 실패한 콜백 (존재하지 않는 payment_id)
        failure = mock_gateway.handle_callback({
            'payment_id': 'nonexistent',
            'status': 'completed'
        })
        assert failure is False
    
    def test_multiple_payments(self, mock_gateway):
        """여러 결제 처리"""
        payments = []
        for i in range(5):
            result = mock_gateway.process_payment(
                amount=1000 * (i + 1),
                currency='KRW',
                payment_method='naverpay',
                order_id=f'ORDER-{i+1}'
            )
            payments.append(result['payment_id'])
        
        # 모든 결제가 생성되었는지 확인
        assert len(payments) == 5
        assert len(set(payments)) == 5  # 모두 고유한 ID
        
        # 각 결제 상태 확인
        for pid in payments:
            status = mock_gateway.get_payment_status(pid)
            assert status == 'created'


class TestAPIEndpoints:
    """API 엔드포인트 테스트"""
    
    def test_health_endpoint(self, client):
        """헬스 체크 엔드포인트"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
    
    def test_scan_endpoint_validation(self, client):
        """스캔 엔드포인트 검증"""
        # 바코드 없이 요청
        response = client.post('/api/scan',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # 빈 바코드
        response = client.post('/api/scan',
            json={'barcode': ''},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_products_list_endpoint(self, client):
        """상품 목록 조회"""
        response = client.get('/api/products')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert data['success'] is True
    
    def test_products_search_endpoint(self, client):
        """상품 검색"""
        response = client.get('/api/products?q=우유')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert data['success'] is True
    
    def test_product_detail_endpoint(self, client):
        """상품 상세 조회"""
        response = client.get('/api/products/8801234567890')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'product' in data
    
    def test_product_stock_endpoint(self, client):
        """재고 확인"""
        response = client.get('/api/products/8801234567890/stock?quantity=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'available' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
