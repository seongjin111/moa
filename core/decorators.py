"""
플랜별 기능 제한 데코레이터
"""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def require_pro_plan(view_func):
    """
    Pro 플랜이 필요한 기능에 사용하는 데코레이터
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': '로그인이 필요합니다.',
                'requires_login': True
            }, status=401)
        
        if not hasattr(request.user, 'profile'):
            return JsonResponse({
                'error': '사용자 프로필을 찾을 수 없습니다.',
                'requires_pro': True
            }, status=403)
        
        if not request.user.profile.is_pro:
            return JsonResponse({
                'error': '이 기능은 Pro 플랜에서만 사용할 수 있습니다.',
                'requires_pro': True,
                'current_plan': request.user.profile.plan
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def check_ai_usage_limit(view_func):
    """
    AI 사용량 제한 확인 데코레이터
    Pro 플랜 사용자의 일일 사용량 제한 확인
    """
    @wraps(view_func)
    @require_pro_plan
    def _wrapped_view(request, *args, **kwargs):
        from django.utils import timezone
        from datetime import timedelta
        from .models import AIPromptUsage
        
        # 오늘 사용량 확인
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_usage = AIPromptUsage.objects.filter(
            user=request.user,
            created_at__gte=today_start
        ).count()
        
        # 일일 제한 (Pro 플랜: 100회)
        daily_limit = 100
        
        if today_usage >= daily_limit:
            return JsonResponse({
                'error': f'일일 AI 사용량 제한에 도달했습니다. (제한: {daily_limit}회)',
                'usage': today_usage,
                'limit': daily_limit,
                'reset_at': (today_start + timedelta(days=1)).isoformat()
            }, status=429)
        
        # 사용량 정보를 request에 추가
        request.ai_usage_today = today_usage
        request.ai_limit_today = daily_limit
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


