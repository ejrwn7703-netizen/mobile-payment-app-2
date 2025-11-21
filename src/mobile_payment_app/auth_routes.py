"""인증 관련 API 라우트

회원가입, 로그인, 토큰 갱신, 프로필 관리
"""

from flask import Blueprint, request, jsonify
from .services.auth import auth_service
from .services.user_repository import user_repository

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """회원가입"""
    data = request.get_json()
    
    # 필수 필드 검증
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'error': 'MISSING_FIELD',
                'message': f'{field}는 필수 항목입니다.'
            }), 400
    
    username = data['username']
    email = data['email']
    password = data['password']
    
    # 입력 검증
    if len(username) < 3:
        return jsonify({
            'error': 'INVALID_USERNAME',
            'message': '사용자명은 3자 이상이어야 합니다.'
        }), 400
    
    if len(password) < 6:
        return jsonify({
            'error': 'INVALID_PASSWORD',
            'message': '비밀번호는 6자 이상이어야 합니다.'
        }), 400
    
    if '@' not in email:
        return jsonify({
            'error': 'INVALID_EMAIL',
            'message': '유효한 이메일 주소를 입력하세요.'
        }), 400
    
    try:
        # 비밀번호 해싱
        password_hash = auth_service.hash_password(password)
        
        # 사용자 생성
        user = user_repository.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role=data.get('role', 'user')  # 기본값: user
        )
        
        # 토큰 생성
        access_token = auth_service.create_access_token(
            user.user_id, user.username, user.role
        )
        refresh_token = auth_service.create_refresh_token(user.user_id)
        
        return jsonify({
            'message': '회원가입이 완료되었습니다.',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    
    except ValueError as e:
        return jsonify({
            'error': 'SIGNUP_FAILED',
            'message': str(e)
        }), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """로그인"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'error': 'MISSING_CREDENTIALS',
            'message': '사용자명과 비밀번호를 입력하세요.'
        }), 400
    
    # 사용자 조회
    user = user_repository.find_by_username(username)
    
    if not user:
        return jsonify({
            'error': 'INVALID_CREDENTIALS',
            'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'
        }), 401
    
    # 비밀번호 검증
    if not auth_service.verify_password(password, user.password_hash):
        return jsonify({
            'error': 'INVALID_CREDENTIALS',
            'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'
        }), 401
    
    # 계정 활성화 확인
    if not user.is_active:
        return jsonify({
            'error': 'ACCOUNT_INACTIVE',
            'message': '비활성화된 계정입니다.'
        }), 403
    
    # 토큰 생성
    access_token = auth_service.create_access_token(
        user.user_id, user.username, user.role
    )
    refresh_token = auth_service.create_refresh_token(user.user_id)
    
    # 마지막 로그인 시간 업데이트
    user_repository.update_last_login(user.user_id)
    
    return jsonify({
        'message': '로그인 성공',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """로그아웃"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({
            'error': 'MISSING_TOKEN',
            'message': 'Refresh token이 필요합니다.'
        }), 400
    
    # Refresh token 무효화
    if auth_service.revoke_refresh_token(refresh_token):
        return jsonify({
            'message': '로그아웃되었습니다.'
        }), 200
    else:
        return jsonify({
            'error': 'INVALID_TOKEN',
            'message': '유효하지 않은 토큰입니다.'
        }), 400


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """토큰 갱신"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({
            'error': 'MISSING_TOKEN',
            'message': 'Refresh token이 필요합니다.'
        }), 400
    
    # 토큰 검증 및 새 토큰 발급
    result = auth_service.refresh_access_token(refresh_token)
    
    if not result:
        return jsonify({
            'error': 'INVALID_TOKEN',
            'message': '유효하지 않거나 만료된 토큰입니다.'
        }), 401
    
    new_access_token, refresh_token = result
    
    return jsonify({
        'access_token': new_access_token,
        'refresh_token': refresh_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
def get_profile():
    """현재 사용자 프로필 조회 (인증 필요)"""
    user_info = auth_service.get_current_user()
    
    if not user_info:
        return jsonify({
            'error': 'UNAUTHORIZED',
            'message': '인증이 필요합니다.'
        }), 401
    
    # 전체 사용자 정보 조회
    user = user_repository.find_by_id(user_info['user_id'])
    
    if not user:
        return jsonify({
            'error': 'USER_NOT_FOUND',
            'message': '사용자를 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['PUT'])
def update_profile():
    """현재 사용자 프로필 업데이트 (인증 필요)"""
    user_info = auth_service.get_current_user()
    
    if not user_info:
        return jsonify({
            'error': 'UNAUTHORIZED',
            'message': '인증이 필요합니다.'
        }), 401
    
    data = request.get_json()
    user_id = user_info['user_id']
    
    # 업데이트 가능한 필드
    update_data = {}
    
    if 'email' in data:
        update_data['email'] = data['email']
    
    if 'password' in data:
        # 새 비밀번호 해싱
        if len(data['password']) < 6:
            return jsonify({
                'error': 'INVALID_PASSWORD',
                'message': '비밀번호는 6자 이상이어야 합니다.'
            }), 400
        update_data['password_hash'] = auth_service.hash_password(data['password'])
    
    # 업데이트
    user = user_repository.update_user(user_id, **update_data)
    
    if not user:
        return jsonify({
            'error': 'UPDATE_FAILED',
            'message': '프로필 업데이트에 실패했습니다.'
        }), 500
    
    return jsonify({
        'message': '프로필이 업데이트되었습니다.',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/users', methods=['GET'])
def list_users():
    """사용자 목록 조회 (관리자 전용)"""
    user_info = auth_service.get_current_user()
    
    if not user_info:
        return jsonify({
            'error': 'UNAUTHORIZED',
            'message': '인증이 필요합니다.'
        }), 401
    
    if user_info.get('role') != 'admin':
        return jsonify({
            'error': 'FORBIDDEN',
            'message': '관리자 권한이 필요합니다.'
        }), 403
    
    # 필터링 옵션
    role = request.args.get('role')
    is_active = request.args.get('is_active')
    
    if is_active is not None:
        is_active = is_active.lower() == 'true'
    
    users = user_repository.list_users(role=role, is_active=is_active)
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': len(users)
    }), 200


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """토큰 검증"""
    user_info = auth_service.get_current_user()
    
    if not user_info:
        return jsonify({
            'valid': False,
            'message': '유효하지 않은 토큰입니다.'
        }), 401
    
    return jsonify({
        'valid': True,
        'user': user_info
    }), 200
