from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
import json

from .models import UserProfile, Team, TeamMember, AIPromptUsage
from .decorators import require_pro_plan, check_ai_usage_limit
from .services.ai_service import AIService


@require_http_methods(["POST"])
@csrf_exempt
def register(request: HttpRequest):
    """
    회원가입 API
    POST /api/auth/register/
    Body: {
        "username": "사용자명",
        "email": "email@example.com",
        "password": "비밀번호",
        "display_name": "표시 이름" (선택)
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip()
        
        # 유효성 검사
        if not username:
            return JsonResponse({'error': '사용자명을 입력해주세요.'}, status=400)
        
        if not email:
            return JsonResponse({'error': '이메일을 입력해주세요.'}, status=400)
        
        if not password:
            return JsonResponse({'error': '비밀번호를 입력해주세요.'}, status=400)
        
        # 이메일 형식 검증
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'error': '올바른 이메일 형식이 아닙니다.'}, status=400)
        
        # 비밀번호 길이 검증
        if len(password) < 8:
            return JsonResponse({'error': '비밀번호는 최소 8자 이상이어야 합니다.'}, status=400)
        
        # 사용자명 중복 확인
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': '이미 사용 중인 사용자명입니다.'}, status=400)
        
        # 이메일 중복 확인
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': '이미 사용 중인 이메일입니다.'}, status=400)
        
        # User 생성
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # UserProfile 업데이트
        if display_name:
            user.profile.display_name = display_name
            user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': user.profile.display_name or user.username,
                'plan': user.profile.plan
            }
        }, status=201)
        
    except IntegrityError:
        return JsonResponse({'error': '이미 존재하는 사용자입니다.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def login_view(request: HttpRequest):
    """
    로그인 API
    POST /api/auth/login/
    Body: {
        "username": "사용자명 또는 이메일",
        "password": "비밀번호"
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({'error': '사용자명과 비밀번호를 입력해주세요.'}, status=400)
        
        # 이메일로도 로그인 가능하도록 처리
        user = None
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': '로그인되었습니다.',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'display_name': user.profile.display_name or user.username,
                        'plan': user.profile.plan,
                        'is_pro': user.profile.is_pro
                    }
                })
            else:
                return JsonResponse({'error': '비활성화된 계정입니다.'}, status=403)
        else:
            return JsonResponse({'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'로그인 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["POST"])
def logout_view(request: HttpRequest):
    """
    로그아웃 API
    POST /api/auth/logout/
    """
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'success': True, 'message': '로그아웃되었습니다.'})
    else:
        return JsonResponse({'error': '로그인되어 있지 않습니다.'}, status=401)


@require_http_methods(["GET"])
def user_info(request: HttpRequest):
    """
    현재 로그인한 사용자 정보 조회
    GET /api/auth/user/
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    user = request.user
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.profile.display_name or user.username,
            'plan': user.profile.plan,
            'is_pro': user.profile.is_pro,
            'notes_count': user.profile.notes_count,
            'email_verified': user.profile.email_verified,
            'created_at': user.date_joined.isoformat() if user.date_joined else None
        }
    })


@require_http_methods(["POST"])
@csrf_exempt
def change_password(request: HttpRequest):
    """
    비밀번호 변경 API
    POST /api/auth/change-password/
    Body: {
        "current_password": "현재 비밀번호",
        "new_password": "새 비밀번호"
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        data = json.loads(request.body) if request.body else {}
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return JsonResponse({'error': '현재 비밀번호와 새 비밀번호를 입력해주세요.'}, status=400)
        
        # 현재 비밀번호 확인
        if not request.user.check_password(current_password):
            return JsonResponse({'error': '현재 비밀번호가 올바르지 않습니다.'}, status=400)
        
        # 새 비밀번호 길이 검증
        if len(new_password) < 8:
            return JsonResponse({'error': '새 비밀번호는 최소 8자 이상이어야 합니다.'}, status=400)
        
        # 비밀번호 변경
        request.user.set_password(new_password)
        request.user.save()
        
        return JsonResponse({'success': True, 'message': '비밀번호가 변경되었습니다.'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'}, status=500)


# ==================== 팀/워크스페이스 API ====================

@require_http_methods(["POST"])
@csrf_exempt
def create_team(request: HttpRequest):
    """
    팀 생성 API
    POST /api/teams/create/
    Body: {
        "name": "팀 이름",
        "description": "팀 설명" (선택),
        "is_public": false (선택)
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        data = json.loads(request.body) if request.body else {}
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        is_public = data.get('is_public', False)
        
        if not name:
            return JsonResponse({'error': '팀 이름을 입력해주세요.'}, status=400)
        
        # 팀 생성
        team = Team.objects.create(
            name=name,
            description=description if description else None,
            owner=request.user,
            is_public=is_public
        )
        
        # 소유자를 owner 역할로 추가
        TeamMember.objects.create(
            team=team,
            user=request.user,
            role='owner',
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': '팀이 생성되었습니다.',
            'team': {
                'id': str(team.id),
                'name': team.name,
                'description': team.description,
                'is_public': team.is_public,
                'invite_code': team.invite_code,
                'owner': {
                    'id': team.owner.id,
                    'username': team.owner.username,
                    'display_name': team.owner.profile.display_name or team.owner.username
                },
                'created_at': team.created_at.isoformat()
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'팀 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def list_teams(request: HttpRequest):
    """
    사용자가 속한 팀 목록 조회
    GET /api/teams/
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    # 사용자가 속한 팀 조회
    memberships = TeamMember.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('team', 'team__owner')
    
    teams = []
    for membership in memberships:
        teams.append({
            'id': str(membership.team.id),
            'name': membership.team.name,
            'description': membership.team.description,
            'is_public': membership.team.is_public,
            'role': membership.role,
            'role_display': membership.get_role_display(),
            'owner': {
                'id': membership.team.owner.id,
                'username': membership.team.owner.username,
                'display_name': membership.team.owner.profile.display_name or membership.team.owner.username
            },
            'notes_count': membership.team.notes_count,
            'members_count': membership.team.members_count,
            'joined_at': membership.joined_at.isoformat(),
            'created_at': membership.team.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'teams': teams,
        'count': len(teams)
    })


@require_http_methods(["GET"])
def get_team(request: HttpRequest, team_id: str):
    """
    팀 상세 정보 조회
    GET /api/teams/{team_id}/
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        team = Team.objects.get(id=team_id)
        
        # 멤버 여부 확인
        try:
            membership = TeamMember.objects.get(team=team, user=request.user, is_active=True)
        except TeamMember.DoesNotExist:
            return JsonResponse({'error': '팀 멤버가 아닙니다.'}, status=403)
        
        # 멤버 목록 조회
        members = TeamMember.objects.filter(
            team=team,
            is_active=True
        ).select_related('user')
        
        members_list = []
        for member in members:
            members_list.append({
                'id': str(member.id),
                'user': {
                    'id': member.user.id,
                    'username': member.user.username,
                    'display_name': member.user.profile.display_name or member.user.username,
                    'email': member.user.email
                },
                'role': member.role,
                'role_display': member.get_role_display(),
                'joined_at': member.joined_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'team': {
                'id': str(team.id),
                'name': team.name,
                'description': team.description,
                'is_public': team.is_public,
                'invite_code': team.invite_code,
                'owner': {
                    'id': team.owner.id,
                    'username': team.owner.username,
                    'display_name': team.owner.profile.display_name or team.owner.username
                },
                'members': members_list,
                'members_count': team.members_count,
                'notes_count': team.notes_count,
                'my_role': membership.role,
                'my_role_display': membership.get_role_display(),
                'created_at': team.created_at.isoformat(),
                'updated_at': team.updated_at.isoformat()
            }
        })
        
    except Team.DoesNotExist:
        return JsonResponse({'error': '팀을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'팀 조회 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def invite_member(request: HttpRequest, team_id: str):
    """
    팀 멤버 초대 API
    POST /api/teams/{team_id}/invite/
    Body: {
        "username": "초대할 사용자명" 또는 "email": "초대할 이메일",
        "role": "member" (선택, 기본값: member)
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        team = Team.objects.get(id=team_id)
        
        # 멤버 여부 및 권한 확인
        try:
            membership = TeamMember.objects.get(team=team, user=request.user, is_active=True)
        except TeamMember.DoesNotExist:
            return JsonResponse({'error': '팀 멤버가 아닙니다.'}, status=403)
        
        if not membership.can_manage_members:
            return JsonResponse({'error': '멤버 초대 권한이 없습니다.'}, status=403)
        
        data = json.loads(request.body) if request.body else {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'member').strip()
        
        # 역할 검증
        valid_roles = ['admin', 'member', 'viewer']
        if role not in valid_roles:
            return JsonResponse({'error': f'유효하지 않은 역할입니다. 가능한 역할: {", ".join(valid_roles)}'}, status=400)
        
        # 소유자는 초대할 수 없음
        if role == 'owner':
            return JsonResponse({'error': '소유자 역할은 초대할 수 없습니다.'}, status=400)
        
        # 사용자 찾기
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'error': '사용자를 찾을 수 없습니다.'}, status=404)
        elif email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'error': '사용자를 찾을 수 없습니다.'}, status=404)
        else:
            return JsonResponse({'error': '사용자명 또는 이메일을 입력해주세요.'}, status=400)
        
        # 이미 멤버인지 확인
        if TeamMember.objects.filter(team=team, user=user).exists():
            existing = TeamMember.objects.get(team=team, user=user)
            if existing.is_active:
                return JsonResponse({'error': '이미 팀 멤버입니다.'}, status=400)
            else:
                # 비활성 멤버 재활성화
                existing.is_active = True
                existing.role = role
                existing.invited_by = request.user
                existing.save()
                return JsonResponse({
                    'success': True,
                    'message': '멤버가 다시 초대되었습니다.',
                    'member': {
                        'id': str(existing.id),
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'display_name': user.profile.display_name or user.username
                        },
                        'role': existing.role
                    }
                })
        
        # 새 멤버 추가
        new_member = TeamMember.objects.create(
            team=team,
            user=user,
            role=role,
            invited_by=request.user,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': '멤버가 초대되었습니다.',
            'member': {
                'id': str(new_member.id),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'display_name': user.profile.display_name or user.username
                },
                'role': new_member.role,
                'role_display': new_member.get_role_display()
            }
        }, status=201)
        
    except Team.DoesNotExist:
        return JsonResponse({'error': '팀을 찾을 수 없습니다.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'멤버 초대 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def join_team_by_code(request: HttpRequest):
    """
    초대 코드로 팀 가입 API
    POST /api/teams/join/
    Body: {
        "invite_code": "초대 코드"
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        data = json.loads(request.body) if request.body else {}
        invite_code = data.get('invite_code', '').strip()
        
        if not invite_code:
            return JsonResponse({'error': '초대 코드를 입력해주세요.'}, status=400)
        
        # 팀 찾기
        try:
            team = Team.objects.get(invite_code=invite_code)
        except Team.DoesNotExist:
            return JsonResponse({'error': '유효하지 않은 초대 코드입니다.'}, status=404)
        
        # 공개 팀이 아니면 초대만 가능
        if not team.is_public:
            return JsonResponse({'error': '이 팀은 공개 팀이 아닙니다. 초대를 받아야 합니다.'}, status=403)
        
        # 이미 멤버인지 확인
        if TeamMember.objects.filter(team=team, user=request.user, is_active=True).exists():
            return JsonResponse({'error': '이미 팀 멤버입니다.'}, status=400)
        
        # 멤버 추가
        new_member = TeamMember.objects.create(
            team=team,
            user=request.user,
            role='member',
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': '팀에 가입되었습니다.',
            'team': {
                'id': str(team.id),
                'name': team.name,
                'description': team.description
            },
            'member': {
                'id': str(new_member.id),
                'role': new_member.role
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'팀 가입 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_member_role(request: HttpRequest, team_id: str, member_id: str):
    """
    멤버 역할 변경 API
    POST /api/teams/{team_id}/members/{member_id}/role/
    Body: {
        "role": "admin" | "member" | "viewer"
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        team = Team.objects.get(id=team_id)
        
        # 권한 확인
        try:
            membership = TeamMember.objects.get(team=team, user=request.user, is_active=True)
        except TeamMember.DoesNotExist:
            return JsonResponse({'error': '팀 멤버가 아닙니다.'}, status=403)
        
        if not membership.can_manage_members:
            return JsonResponse({'error': '멤버 관리 권한이 없습니다.'}, status=403)
        
        # 대상 멤버 찾기
        try:
            target_member = TeamMember.objects.get(id=member_id, team=team, is_active=True)
        except TeamMember.DoesNotExist:
            return JsonResponse({'error': '멤버를 찾을 수 없습니다.'}, status=404)
        
        # 소유자 역할은 변경 불가
        if target_member.role == 'owner':
            return JsonResponse({'error': '소유자 역할은 변경할 수 없습니다.'}, status=400)
        
        # 소유자만 소유자 역할 부여 가능
        if membership.role != 'owner':
            return JsonResponse({'error': '소유자만 역할을 변경할 수 있습니다.'}, status=403)
        
        data = json.loads(request.body) if request.body else {}
        new_role = data.get('role', '').strip()
        
        valid_roles = ['admin', 'member', 'viewer']
        if new_role not in valid_roles:
            return JsonResponse({'error': f'유효하지 않은 역할입니다. 가능한 역할: {", ".join(valid_roles)}'}, status=400)
        
        target_member.role = new_role
        target_member.save()
        
        return JsonResponse({
            'success': True,
            'message': '멤버 역할이 변경되었습니다.',
            'member': {
                'id': str(target_member.id),
                'user': {
                    'id': target_member.user.id,
                    'username': target_member.user.username,
                    'display_name': target_member.user.profile.display_name or target_member.user.username
                },
                'role': target_member.role,
                'role_display': target_member.get_role_display()
            }
        })
        
    except Team.DoesNotExist:
        return JsonResponse({'error': '팀을 찾을 수 없습니다.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'역할 변경 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def remove_member(request: HttpRequest, team_id: str, member_id: str):
    """
    멤버 제거 API
    POST /api/teams/{team_id}/members/{member_id}/remove/
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    try:
        team = Team.objects.get(id=team_id)
        
        # 권한 확인
        try:
            membership = TeamMember.objects.get(team=team, user=request.user, is_active=True)
        except TeamMember.DoesNotExist:
            return JsonResponse({'error': '팀 멤버가 아닙니다.'}, status=403)
        
        if not membership.can_manage_members:
            return JsonResponse({'error': '멤버 제거 권한이 없습니다.'}, status=403)
        
        # 대상 멤버 찾기
        try:
            target_member = TeamMember.objects.get(id=member_id, team=team, is_active=True)
        except TeamMember.DoesNotExist:
            return JsonResponse({'error': '멤버를 찾을 수 없습니다.'}, status=404)
        
        # 소유자는 제거 불가
        if target_member.role == 'owner':
            return JsonResponse({'error': '소유자는 제거할 수 없습니다.'}, status=400)
        
        # 자기 자신 제거 가능
        if target_member.user == request.user:
            target_member.is_active = False
            target_member.save()
            return JsonResponse({
                'success': True,
                'message': '팀에서 나갔습니다.'
            })
        
        # 다른 멤버 제거
        target_member.is_active = False
        target_member.save()
        
        return JsonResponse({
            'success': True,
            'message': '멤버가 제거되었습니다.'
        })
        
    except Team.DoesNotExist:
        return JsonResponse({'error': '팀을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'멤버 제거 중 오류가 발생했습니다: {str(e)}'}, status=500)


# ==================== AI 프롬프트 API ====================

@require_http_methods(["POST"])
@csrf_exempt
@check_ai_usage_limit
def ai_prompt(request: HttpRequest):
    """
    AI 프롬프트 API (Pro 플랜 전용)
    POST /api/ai/prompt/
    Body: {
        "prompt": "프롬프트 내용",
        "provider": "openai" | "claude" (선택, 기본값: openai),
        "model": "모델명" (선택),
        "max_tokens": 1000 (선택)
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        prompt = data.get('prompt', '').strip()
        provider = data.get('provider', 'openai').strip().lower()
        model = data.get('model', '').strip()
        max_tokens = data.get('max_tokens', 1000)
        
        if not prompt:
            return JsonResponse({'error': '프롬프트를 입력해주세요.'}, status=400)
        
        # 제공자 검증
        if provider not in ['openai', 'claude']:
            return JsonResponse({'error': '지원하지 않는 AI 제공자입니다. (openai 또는 claude)'}, status=400)
        
        # AI 호출
        result = AIService.call_ai(prompt, provider, model, max_tokens)
        
        if not result.get('success'):
            return JsonResponse({'error': result.get('error', 'AI 호출 실패')}, status=500)
        
        # 사용량 기록
        try:
            cost = AIService.estimate_cost(result['tokens_used'], provider, result['model'])
            
            usage = AIPromptUsage.objects.create(
                user=request.user,
                prompt=prompt,
                response=result['response'],
                provider=provider,
                model=result['model'],
                tokens_used=result['tokens_used'],
                cost=cost
            )
            
            # 오늘 사용량 정보
            today_usage = getattr(request, 'ai_usage_today', 0) + 1
            today_limit = getattr(request, 'ai_limit_today', 100)
            
            return JsonResponse({
                'success': True,
                'response': result['response'],
                'usage': {
                    'id': str(usage.id),
                    'tokens_used': result['tokens_used'],
                    'cost': float(cost),
                    'provider': provider,
                    'model': result['model']
                },
                'quota': {
                    'used_today': today_usage,
                    'limit_today': today_limit,
                    'remaining_today': today_limit - today_usage
                }
            })
        except Exception as e:
            # 사용량 기록 실패해도 응답은 반환
            return JsonResponse({
                'success': True,
                'response': result['response'],
                'warning': f'사용량 기록 중 오류가 발생했습니다: {str(e)}'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'AI 프롬프트 처리 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def ai_usage_stats(request: HttpRequest):
    """
    AI 사용량 통계 조회 API
    GET /api/ai/usage/
    Query params: ?days=7 (선택, 기본값: 7일)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    if not request.user.profile.is_pro:
        return JsonResponse({'error': 'Pro 플랜에서만 사용할 수 있습니다.'}, status=403)
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # 사용량 조회
        usages = AIPromptUsage.objects.filter(
            user=request.user,
            created_at__gte=start_date
        ).order_by('-created_at')
        
        # 통계 계산
        total_requests = usages.count()
        total_tokens = sum(u.tokens_used for u in usages)
        total_cost = sum(float(u.cost) for u in usages)
        
        # 제공자별 통계
        provider_stats = {}
        for usage in usages:
            provider = usage.provider
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'count': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            provider_stats[provider]['count'] += 1
            provider_stats[provider]['tokens'] += usage.tokens_used
            provider_stats[provider]['cost'] += float(usage.cost)
        
        # 최근 사용 내역 (최대 20개)
        recent_usages = []
        for usage in usages[:20]:
            recent_usages.append({
                'id': str(usage.id),
                'prompt': usage.prompt[:100] + '...' if len(usage.prompt) > 100 else usage.prompt,
                'provider': usage.provider,
                'model': usage.model,
                'tokens_used': usage.tokens_used,
                'cost': float(usage.cost),
                'created_at': usage.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'period_days': days,
            'summary': {
                'total_requests': total_requests,
                'total_tokens': total_tokens,
                'total_cost': round(total_cost, 6),
                'average_tokens_per_request': round(total_tokens / total_requests, 2) if total_requests > 0 else 0
            },
            'by_provider': provider_stats,
            'recent_usages': recent_usages
        })
        
    except ValueError:
        return JsonResponse({'error': '잘못된 days 파라미터입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'통계 조회 중 오류가 발생했습니다: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def ai_usage_today(request: HttpRequest):
    """
    오늘 AI 사용량 조회 API
    GET /api/ai/usage/today/
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    if not request.user.profile.is_pro:
        return JsonResponse({'error': 'Pro 플랜에서만 사용할 수 있습니다.'}, status=403)
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_usage = AIPromptUsage.objects.filter(
            user=request.user,
            created_at__gte=today_start
        )
        
        count = today_usage.count()
        total_tokens = sum(u.tokens_used for u in today_usage)
        total_cost = sum(float(u.cost) for u in today_usage)
        
        daily_limit = 100
        
        return JsonResponse({
            'success': True,
            'usage': {
                'count': count,
                'tokens': total_tokens,
                'cost': round(total_cost, 6)
            },
            'limit': {
                'daily': daily_limit,
                'remaining': daily_limit - count
            },
            'reset_at': (today_start + timedelta(days=1)).isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'사용량 조회 중 오류가 발생했습니다: {str(e)}'}, status=500)
