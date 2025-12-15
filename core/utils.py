"""
권한 검증 유틸리티 함수
"""

from django.http import HttpRequest
from .models import Team, TeamMember


def get_team_membership(user, team):
    """
    사용자의 팀 멤버십 조회
    Returns: TeamMember 객체 또는 None
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        return TeamMember.objects.get(team=team, user=user, is_active=True)
    except TeamMember.DoesNotExist:
        return None


def can_edit_team(user, team):
    """
    팀 설정 편집 권한 확인
    """
    membership = get_team_membership(user, team)
    if not membership:
        return False
    return membership.can_edit_team


def can_manage_members(user, team):
    """
    멤버 관리 권한 확인
    """
    membership = get_team_membership(user, team)
    if not membership:
        return False
    return membership.can_manage_members


def can_create_note(user, team):
    """
    팀 노트 생성 권한 확인
    """
    if not team:
        return True  # 개인 노트는 항상 생성 가능
    
    membership = get_team_membership(user, team)
    if not membership:
        return False
    return membership.can_create_note


def can_edit_note(user, note):
    """
    노트 편집 권한 확인
    """
    # 개인 노트인 경우
    if not note.team:
        # 소유자 확인
        if note.owner == user:
            return True
        # 비회원 노트는 client_token으로 확인 (뷰에서 처리)
        return False
    
    # 팀 노트인 경우
    membership = get_team_membership(user, note.team)
    if not membership:
        return False
    return membership.can_edit_note


def can_view_note(user, note):
    """
    노트 조회 권한 확인
    """
    # 개인 노트인 경우
    if not note.team:
        # 소유자 확인
        if note.owner == user:
            return True
        # 비회원 노트는 client_token으로 확인 (뷰에서 처리)
        return False
    
    # 팀 노트인 경우
    membership = get_team_membership(user, note.team)
    if not membership:
        return False
    return membership.can_view_note


