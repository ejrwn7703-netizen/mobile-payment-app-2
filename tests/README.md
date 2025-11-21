# 테스트 실행 가이드

## 📋 테스트 개요

이 프로젝트는 총 3개의 테스트 파일로 구성되어 있습니다:

1. **test_barcode.py** - 바코드 스캔 기능 테스트 (18개 테스트)
2. **test_payment_integration.py** - 결제 통합 테스트 (신규 추가, 30개 테스트)
3. **test_error_handling.py** - 에러 처리 테스트 (신규 추가, 35개 테스트)

**총 테스트 케이스**: 83개

## 🚀 테스트 실행 방법

### 전체 테스트 실행

```bash
pytest tests/ -v
```

### 특정 파일만 실행

```bash
# 바코드 테스트만
pytest tests/test_barcode.py -v

# 결제 통합 테스트만
pytest tests/test_payment_integration.py -v

# 에러 처리 테스트만
pytest tests/test_error_handling.py -v
```

### 커버리지 포함 실행

```bash
pytest tests/ --cov=src/mobile_payment_app --cov-report=html --cov-report=term
```

실행 후 `htmlcov/index.html` 파일을 브라우저에서 열면 상세한 커버리지 리포트를 볼 수 있습니다.

### 특정 테스트 클래스만 실행

```bash
pytest tests/test_payment_integration.py::TestPaymentFlow -v
```

### 특정 테스트 함수만 실행

```bash
pytest tests/test_payment_integration.py::TestPaymentFlow::test_complete_payment_flow -v
```

### 실패한 테스트만 재실행

```bash
pytest --lf  # last-failed
```

### 빠른 테스트 (첫 실패에서 중단)

```bash
pytest -x
```

## 📊 커버리지 목표

- **목표 커버리지**: 80% 이상
- **핵심 모듈 커버리지**: 90% 이상
  - `services/barcode.py`
  - `services/naverpay.py`
  - `routes.py`

## 🧪 테스트 카테고리

### 1. 단위 테스트 (Unit Tests)
- `TestBarcodeScanner` - 바코드 스캔 로직
- `TestNaverPayGateway` - 결제 게이트웨이 로직

### 2. 통합 테스트 (Integration Tests)
- `TestPaymentFlow` - 전체 결제 플로우
- `TestAPIEndpoints` - API 엔드포인트

### 3. 에러 처리 테스트 (Error Handling)
- `TestBarcodeErrorHandling` - 바코드 에러
- `TestPaymentErrorHandling` - 결제 에러
- `TestAPIErrorResponses` - API 에러 응답

### 4. 엣지 케이스 테스트 (Edge Cases)
- `TestPaymentEdgeCases` - 결제 엣지 케이스
- `TestDataValidation` - 데이터 검증

### 5. 동시성 테스트 (Concurrency)
- `TestConcurrency` - 동시 요청 처리

## 📝 테스트 작성 가이드라인

### 테스트 명명 규칙

```python
def test_<기능>_<상황>_<예상결과>(self):
    """테스트 설명"""
    # Arrange (준비)
    # Act (실행)
    # Assert (검증)
```

예시:
```python
def test_scan_product_with_invalid_barcode_returns_error(self):
    """잘못된 바코드로 스캔 시 에러 반환"""
    result = self.scanner.scan_product("invalid")
    assert result["success"] is False
```

### Fixture 사용

```python
@pytest.fixture
def client():
    """테스트 클라이언트"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

### 파라미터화된 테스트

```python
@pytest.mark.parametrize("barcode,expected", [
    ("8801234567890", True),
    ("invalid", False),
    ("", False),
])
def test_validate_barcodes(self, barcode, expected):
    result = self.scanner.validate_barcode(barcode)
    assert result["valid"] == expected
```

## 🔧 테스트 환경 설정

### 필요한 패키지

```bash
pip install pytest pytest-cov
```

### pytest 설정 (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 📈 커버리지 확인

### 터미널에서 커버리지 확인

```bash
pytest --cov=src/mobile_payment_app --cov-report=term-missing
```

출력 예시:
```
Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
src/mobile_payment_app/__init__.py           0      0   100%
src/mobile_payment_app/app.py               25      2    92%   45-46
src/mobile_payment_app/routes.py            85      8    91%   102-109
src/mobile_payment_app/services/barcode.py  120      5    96%   78, 145-148
src/mobile_payment_app/services/naverpay.py 180     25    86%   multiple
-----------------------------------------------------------------------
TOTAL                                       410     40    90%
```

### HTML 리포트 생성

```bash
pytest --cov=src/mobile_payment_app --cov-report=html
```

브라우저에서 `htmlcov/index.html` 열기

## 🐛 디버깅

### 실패한 테스트 디버깅

```bash
# 상세한 traceback
pytest -v --tb=long

# PDB 디버거 실행
pytest --pdb

# 특정 테스트만 디버깅
pytest tests/test_payment_integration.py::TestPaymentFlow::test_complete_payment_flow --pdb
```

### 출력 확인

```bash
# print 문 출력 보기
pytest -s

# 로그 출력 보기
pytest --log-cli-level=INFO
```

## ⚡ 성능 테스트

### 가장 느린 테스트 찾기

```bash
pytest --durations=10
```

### 병렬 실행 (pytest-xdist 사용)

```bash
pip install pytest-xdist
pytest -n auto  # CPU 코어 수만큼 병렬 실행
```

## 📋 체크리스트

실행 전 확인사항:

- [ ] 가상 환경 활성화
- [ ] 모든 의존성 설치 (`pip install -r requirements.txt`)
- [ ] 서버가 실행 중이지 않은지 확인 (포트 충돌 방지)
- [ ] `data/` 디렉토리 존재 확인

## 🎯 CI/CD 통합

### GitHub Actions 예시

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ --cov=src/mobile_payment_app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📞 문제 해결

### 자주 발생하는 문제

1. **ModuleNotFoundError**
   ```bash
   # 프로젝트 루트에서 실행
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   pytest tests/
   ```

2. **Fixture not found**
   - `conftest.py` 파일 확인
   - Fixture 이름 오타 확인

3. **테스트 실패 (AssertionError)**
   - 예상 값과 실제 값 비교
   - `--tb=long` 옵션으로 상세 정보 확인

## 📚 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 문서](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
