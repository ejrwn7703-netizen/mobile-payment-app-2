# 네이버페이 연동 가이드

## 설정 방법

### 1. 네이버페이 가맹점 등록

1. [네이버페이 개발자센터](https://developer.pay.naver.com) 접속
2. 가맹점 신청 및 승인
3. Client ID와 Client Secret 발급

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정:

```bash
# 네이버페이 API 인증 정보
NAVER_PAY_CLIENT_ID=your_client_id_here
NAVER_PAY_CLIENT_SECRET=your_client_secret_here

# 실행 모드 선택
# - mock: 로컬 개발용 Mock (기본값)
# - sandbox: 네이버페이 테스트 환경
# - production: 실제 결제 환경
NAVER_PAY_MODE=mock

# 애플리케이션 URL
APP_BASE_URL=http://127.0.0.1:8000
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 모드별 동작

#### Mock 모드 (기본)
```python
# .env 파일
NAVER_PAY_MODE=mock

# 또는 코드에서
gateway = NaverPayGateway(mode="mock")
```
- 로컬 파일 기반 Mock 결제
- Client ID/Secret 불필요
- 즉시 테스트 가능

#### Sandbox 모드 (테스트)
```python
# .env 파일
NAVER_PAY_MODE=sandbox
NAVER_PAY_CLIENT_ID=test_client_id
NAVER_PAY_CLIENT_SECRET=test_client_secret

# 또는 코드에서
gateway = NaverPayGateway(
    client_id="test_client_id",
    client_secret="test_client_secret",
    mode="sandbox"
)
```
- 네이버페이 테스트 API 호출
- 실제 결제 없이 플로우 테스트
- Client ID/Secret 필수

#### Production 모드 (실제 결제)
```python
# .env 파일
NAVER_PAY_MODE=production
NAVER_PAY_CLIENT_ID=live_client_id
NAVER_PAY_CLIENT_SECRET=live_client_secret

# 또는 코드에서
gateway = NaverPayGateway(
    client_id="live_client_id",
    client_secret="live_client_secret",
    mode="production"
)
```
- 실제 네이버페이 결제 처리
- 실제 금액 청구
- 운영 환경 Client ID/Secret 필수

## API 사용 예시

### 결제 요청
```python
result = gateway.process_payment(
    amount=10000,
    currency="KRW",
    payment_method="NAVERPAY",
    order_id="ORDER-123",
    return_url="http://yourapp.com/payment/complete"
)

print(result)
# {
#     "payment_id": "PAY-xxx",
#     "redirect_url": "https://pay.naver.com/payments/..."
# }
```

### 결제 상태 조회
```python
status = gateway.get_payment_status("PAY-xxx")
print(status)  # "reserved", "completed", "cancelled", "failed"
```

### 결제 승인
```python
result = gateway.approve_payment("PAY-xxx")
print(result)
# {"success": True, "payment_id": "PAY-xxx", "status": "completed"}
```

### 결제 취소
```python
result = gateway.cancel_payment(
    payment_id="PAY-xxx",
    reason="고객 요청",
    amount=10000  # 부분 취소 시 금액 지정
)
```

### 콜백 처리
```python
# 네이버페이로부터 콜백 수신
payload = {
    "paymentId": "PAY-xxx",
    "paymentStatus": "APPROVED",
    "signature": "..."
}

success = gateway.handle_callback(payload)
```

## 보안 고려사항

1. **환경 변수 사용**: Client Secret은 절대 코드에 하드코딩하지 말 것
2. **HTTPS 필수**: Production 모드는 반드시 HTTPS 사용
3. **서명 검증**: 콜백 수신 시 서명 검증 필수
4. **IP 화이트리스트**: 네이버페이 서버 IP만 콜백 허용

## 트러블슈팅

### Mock 모드에서 테스트
Client ID가 없어도 Mock 모드로 전체 플로우 테스트 가능:
```bash
NAVER_PAY_MODE=mock python -m src.mobile_payment_app.app
```

### Sandbox 연결 실패
- Client ID/Secret 확인
- 네이버페이 개발자센터에서 Sandbox 설정 확인
- 네트워크 방화벽 확인

### Production 결제 실패
- 가맹점 심사 완료 여부 확인
- 정산 계좌 등록 확인
- 결제 한도 확인

## 참고 문서

- [네이버페이 개발자 문서](https://developer.pay.naver.com/docs)
- [결제 연동 가이드](https://developer.pay.naver.com/docs/v2/api)
