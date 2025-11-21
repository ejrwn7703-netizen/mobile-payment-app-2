"""사용자 모델 및 저장소

JSON 파일 기반 사용자 데이터 관리
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional


# 사용자 데이터 저장 경로
DEFAULT_USERS_PATH = os.environ.get("USERS_STORE", "data/users.json")


def _ensure_dir(path: str):
    """디렉토리 생성"""
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _load_users(path: str) -> Dict[str, Dict]:
    """사용자 데이터 로드"""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(path: str, users: Dict[str, Dict]):
    """사용자 데이터 저장"""
    _ensure_dir(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class User:
    """사용자 모델"""
    
    def __init__(self, user_id: str, username: str, email: str, 
                 password_hash: str, role: str = 'user', **kwargs):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.is_active = kwargs.get('is_active', True)
        self.last_login = kwargs.get('last_login')
    
    def to_dict(self, include_password: bool = False) -> Dict:
        """딕셔너리로 변환"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active,
            'last_login': self.last_login
        }
        
        if include_password:
            data['password_hash'] = self.password_hash
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """딕셔너리에서 생성"""
        return cls(**data)


class UserRepository:
    """사용자 저장소"""
    
    def __init__(self, store_path: str = None):
        self.store_path = store_path or DEFAULT_USERS_PATH
        self._users = _load_users(self.store_path)
        
        # 초기 관리자 계정 생성 (데이터가 비어있을 경우)
        if not self._users:
            self._create_default_admin()
    
    def _persist(self):
        """파일에 저장"""
        _save_users(self.store_path, self._users)
    
    def _create_default_admin(self):
        """기본 관리자 계정 생성"""
        from .auth import auth_service
        
        admin_id = 'admin-' + uuid.uuid4().hex[:8]
        admin = User(
            user_id=admin_id,
            username='admin',
            email='admin@example.com',
            password_hash=auth_service.hash_password('admin123'),
            role='admin'
        )
        
        self._users[admin_id] = admin.to_dict(include_password=True)
        self._persist()
    
    def create_user(self, username: str, email: str, password_hash: str, 
                   role: str = 'user') -> User:
        """사용자 생성"""
        # 중복 확인
        if self.find_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        
        if self.find_by_email(email):
            raise ValueError(f"Email '{email}' already exists")
        
        user_id = 'user-' + uuid.uuid4().hex[:12]
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role
        )
        
        self._users[user_id] = user.to_dict(include_password=True)
        self._persist()
        
        return user
    
    def find_by_id(self, user_id: str) -> Optional[User]:
        """ID로 사용자 조회"""
        data = self._users.get(user_id)
        if data:
            return User.from_dict(data)
        return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 조회"""
        for user_data in self._users.values():
            if user_data.get('username') == username:
                return User.from_dict(user_data)
        return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """이메일로 조회"""
        for user_data in self._users.values():
            if user_data.get('email') == email:
                return User.from_dict(user_data)
        return None
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """사용자 정보 업데이트"""
        if user_id not in self._users:
            return None
        
        user_data = self._users[user_id]
        
        # 업데이트 가능한 필드
        allowed_fields = ['username', 'email', 'password_hash', 'role', 'is_active']
        
        for field in allowed_fields:
            if field in kwargs:
                user_data[field] = kwargs[field]
        
        user_data['updated_at'] = datetime.utcnow().isoformat()
        
        self._users[user_id] = user_data
        self._persist()
        
        return User.from_dict(user_data)
    
    def update_last_login(self, user_id: str):
        """마지막 로그인 시간 업데이트"""
        if user_id in self._users:
            self._users[user_id]['last_login'] = datetime.utcnow().isoformat()
            self._persist()
    
    def delete_user(self, user_id: str) -> bool:
        """사용자 삭제"""
        if user_id in self._users:
            del self._users[user_id]
            self._persist()
            return True
        return False
    
    def list_users(self, role: str = None, is_active: bool = None) -> List[User]:
        """사용자 목록 조회"""
        users = []
        
        for user_data in self._users.values():
            # 필터링
            if role and user_data.get('role') != role:
                continue
            if is_active is not None and user_data.get('is_active') != is_active:
                continue
            
            users.append(User.from_dict(user_data))
        
        return users
    
    def count_users(self) -> int:
        """전체 사용자 수"""
        return len(self._users)


# 전역 인스턴스
user_repository = UserRepository()
