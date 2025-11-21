"""JWT 인증 서비스

JWT 토큰 생성/검증, 비밀번호 해싱, 사용자 인증 처리
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, jsonify


class AuthService:
    """JWT 기반 인증 서비스"""
    
    def __init__(self):
        # JWT 비밀 키 (환경변수에서 로드, 없으면 랜덤 생성)
        self.secret_key = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)
        self.algorithm = 'HS256'
        
        # 토큰 만료 시간 (기본값)
        self.access_token_expire_minutes = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        self.refresh_token_expire_days = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        
        # Refresh token 저장소 (실제로는 Redis 등 사용 권장)
        self._refresh_tokens = {}
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해싱 (SHA-256 + Salt)"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        try:
            salt, pwd_hash = hashed.split('$')
            return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
        except (ValueError, AttributeError):
            return False
    
    def create_access_token(self, user_id: str, username: str, role: str = 'user') -> str:
        """Access Token 생성"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Refresh Token 생성"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        token_id = secrets.token_urlsafe(32)
        
        payload = {
            'user_id': user_id,
            'token_id': token_id,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Refresh token 저장 (블랙리스트 관리용)
        self._refresh_tokens[token_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'expires_at': expire
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """토큰 검증 및 페이로드 반환"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Refresh token인 경우 블랙리스트 확인
            if payload.get('type') == 'refresh':
                token_id = payload.get('token_id')
                if token_id not in self._refresh_tokens:
                    return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None  # 토큰 만료
        except jwt.InvalidTokenError:
            return None  # 잘못된 토큰
    
    def revoke_refresh_token(self, token: str) -> bool:
        """Refresh token 무효화 (로그아웃)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get('token_id')
            
            if token_id in self._refresh_tokens:
                del self._refresh_tokens[token_id]
                return True
            return False
        except jwt.InvalidTokenError:
            return False
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh token으로 새 Access token 발급"""
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get('type') != 'refresh':
            return None
        
        user_id = payload.get('user_id')
        
        # 새 토큰 발급 (user 정보는 별도 조회 필요)
        # 여기서는 간단히 user_id만 사용
        new_access_token = self.create_access_token(user_id, user_id)
        
        return new_access_token, refresh_token
    
    def get_current_user(self) -> Optional[Dict]:
        """현재 요청의 사용자 정보 추출"""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = self.verify_token(token)
        
        if not payload or payload.get('type') != 'access':
            return None
        
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': payload.get('role', 'user')
        }
    
    def token_required(self, f):
        """인증 필수 데코레이터"""
        @wraps(f)
        def decorated(*args, **kwargs):
            user = self.get_current_user()
            
            if not user:
                return jsonify({
                    'error': 'UNAUTHORIZED',
                    'message': '인증이 필요합니다.'
                }), 401
            
            # 함수에 user 정보 전달
            return f(user=user, *args, **kwargs)
        
        return decorated
    
    def admin_required(self, f):
        """관리자 권한 필수 데코레이터"""
        @wraps(f)
        def decorated(*args, **kwargs):
            user = self.get_current_user()
            
            if not user:
                return jsonify({
                    'error': 'UNAUTHORIZED',
                    'message': '인증이 필요합니다.'
                }), 401
            
            if user.get('role') != 'admin':
                return jsonify({
                    'error': 'FORBIDDEN',
                    'message': '관리자 권한이 필요합니다.'
                }), 403
            
            return f(user=user, *args, **kwargs)
        
        return decorated
    
    def cleanup_expired_tokens(self):
        """만료된 refresh token 정리"""
        now = datetime.utcnow()
        expired_tokens = [
            token_id for token_id, data in self._refresh_tokens.items()
            if data['expires_at'] < now
        ]
        
        for token_id in expired_tokens:
            del self._refresh_tokens[token_id]
        
        return len(expired_tokens)


# 전역 인스턴스
auth_service = AuthService()
