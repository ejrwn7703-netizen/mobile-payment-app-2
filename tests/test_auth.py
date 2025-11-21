"""JWT 인증 시스템 테스트

회원가입, 로그인, 토큰 검증, 프로필 관리 등
"""

import pytest
import json
from src.mobile_payment_app.app import app
from src.mobile_payment_app.services.user_repository import user_repository
from src.mobile_payment_app.services.auth import auth_service


@pytest.fixture
def client():
    """Flask 테스트 클라이언트"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_user():
    """테스트용 사용자 생성"""
    import time
    import random
    username = f"testuser_{int(time.time())}_{random.randint(1000, 9999)}"
    email = f"{username}@test.com"
    password = "testpass123"
    
    yield {
        'username': username,
        'email': email,
        'password': password
    }


class TestSignup:
    """회원가입 테스트"""
    
    def test_signup_success(self, client, test_user):
        """정상 회원가입"""
        response = client.post('/api/auth/signup', 
                               json=test_user,
                               content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'user' in data
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == test_user['username']
        assert data['user']['email'] == test_user['email']
    
    def test_signup_missing_fields(self, client):
        """필수 필드 누락"""
        response = client.post('/api/auth/signup',
                               json={'username': 'test'},
                               content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'MISSING_FIELD'
    
    def test_signup_short_username(self, client, test_user):
        """짧은 사용자명"""
        test_user['username'] = 'ab'
        response = client.post('/api/auth/signup',
                               json=test_user,
                               content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'INVALID_USERNAME'
    
    def test_signup_short_password(self, client, test_user):
        """짧은 비밀번호"""
        test_user['password'] = '12345'
        response = client.post('/api/auth/signup',
                               json=test_user,
                               content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'INVALID_PASSWORD'
    
    def test_signup_invalid_email(self, client, test_user):
        """잘못된 이메일"""
        test_user['email'] = 'invalid-email'
        response = client.post('/api/auth/signup',
                               json=test_user,
                               content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'INVALID_EMAIL'
    
    def test_signup_duplicate_username(self, client, test_user):
        """중복 사용자명"""
        # 첫 번째 회원가입
        client.post('/api/auth/signup', json=test_user, content_type='application/json')
        
        # 두 번째 회원가입 (같은 username)
        response = client.post('/api/auth/signup',
                               json=test_user,
                               content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['message']


class TestLogin:
    """로그인 테스트"""
    
    def test_login_success(self, client, test_user):
        """정상 로그인"""
        # 회원가입
        client.post('/api/auth/signup', json=test_user, content_type='application/json')
        
        # 로그인
        response = client.post('/api/auth/login',
                               json={
                                   'username': test_user['username'],
                                   'password': test_user['password']
                               },
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == test_user['username']
    
    def test_login_invalid_username(self, client):
        """존재하지 않는 사용자"""
        response = client.post('/api/auth/login',
                               json={
                                   'username': 'nonexistent',
                                   'password': 'password123'
                               },
                               content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'INVALID_CREDENTIALS'
    
    def test_login_wrong_password(self, client, test_user):
        """잘못된 비밀번호"""
        # 회원가입
        client.post('/api/auth/signup', json=test_user, content_type='application/json')
        
        # 잘못된 비밀번호로 로그인
        response = client.post('/api/auth/login',
                               json={
                                   'username': test_user['username'],
                                   'password': 'wrongpassword'
                               },
                               content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'INVALID_CREDENTIALS'
    
    def test_login_missing_credentials(self, client):
        """자격 증명 누락"""
        response = client.post('/api/auth/login',
                               json={'username': 'test'},
                               content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'MISSING_CREDENTIALS'


class TestTokenOperations:
    """토큰 관련 테스트"""
    
    def test_token_verification(self, client, test_user):
        """토큰 검증"""
        # 회원가입 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        token = json.loads(signup_response.data)['access_token']
        
        # 토큰 검증
        response = client.get('/api/auth/verify',
                              headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] is True
        assert data['user']['username'] == test_user['username']
    
    def test_token_verification_no_token(self, client):
        """토큰 없이 검증"""
        response = client.get('/api/auth/verify')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['valid'] is False
    
    def test_token_refresh(self, client, test_user):
        """토큰 갱신"""
        # 로그인 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        refresh_token = json.loads(signup_response.data)['refresh_token']
        
        # 토큰 갱신
        response = client.post('/api/auth/refresh',
                               json={'refresh_token': refresh_token},
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_token_refresh_invalid_token(self, client):
        """잘못된 refresh token"""
        response = client.post('/api/auth/refresh',
                               json={'refresh_token': 'invalid_token'},
                               content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'INVALID_TOKEN'


class TestProfile:
    """프로필 관리 테스트"""
    
    def test_get_profile(self, client, test_user):
        """프로필 조회"""
        # 회원가입 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        token = json.loads(signup_response.data)['access_token']
        
        # 프로필 조회
        response = client.get('/api/auth/me',
                              headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['username'] == test_user['username']
        assert data['user']['email'] == test_user['email']
    
    def test_get_profile_unauthorized(self, client):
        """인증 없이 프로필 조회"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'UNAUTHORIZED'
    
    def test_update_profile(self, client, test_user):
        """프로필 업데이트"""
        # 회원가입 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        token = json.loads(signup_response.data)['access_token']
        
        # 프로필 업데이트
        new_email = 'newemail@test.com'
        response = client.put('/api/auth/me',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'email': new_email},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['email'] == new_email
    
    def test_update_password(self, client, test_user):
        """비밀번호 업데이트"""
        # 회원가입 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        token = json.loads(signup_response.data)['access_token']
        
        # 비밀번호 변경
        new_password = 'newpassword123'
        response = client.put('/api/auth/me',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'password': new_password},
                              content_type='application/json')
        
        assert response.status_code == 200
        
        # 새 비밀번호로 로그인 시도
        login_response = client.post('/api/auth/login',
                                     json={
                                         'username': test_user['username'],
                                         'password': new_password
                                     },
                                     content_type='application/json')
        
        assert login_response.status_code == 200


class TestLogout:
    """로그아웃 테스트"""
    
    def test_logout_success(self, client, test_user):
        """정상 로그아웃"""
        # 로그인 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        refresh_token = json.loads(signup_response.data)['refresh_token']
        
        # 로그아웃
        response = client.post('/api/auth/logout',
                               json={'refresh_token': refresh_token},
                               content_type='application/json')
        
        assert response.status_code == 200
        
        # 로그아웃 후 토큰 갱신 시도 (실패해야 함)
        refresh_response = client.post('/api/auth/refresh',
                                       json={'refresh_token': refresh_token},
                                       content_type='application/json')
        
        assert refresh_response.status_code == 401


class TestAuthenticatedPayment:
    """인증된 결제 테스트"""
    
    def test_payment_with_authentication(self, client, test_user):
        """로그인된 사용자의 결제"""
        # 회원가입 및 토큰 획득
        signup_response = client.post('/api/auth/signup',
                                      json=test_user,
                                      content_type='application/json')
        token = json.loads(signup_response.data)['access_token']
        
        # 인증된 결제 요청
        payment_data = {
            'amount': 10000,
            'currency': 'KRW',
            'payment_method': 'naverpay'
        }
        
        response = client.post('/api/payments',
                               headers={'Authorization': f'Bearer {token}'},
                               json=payment_data,
                               content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'payment_id' in data
        assert data['user'] == test_user['username']
    
    def test_payment_without_authentication(self, client):
        """게스트 결제 (인증 없음)"""
        payment_data = {
            'amount': 10000,
            'currency': 'KRW',
            'payment_method': 'naverpay'
        }
        
        response = client.post('/api/payments',
                               json=payment_data,
                               content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['user'] == 'guest'
