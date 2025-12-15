from django.urls import path
from . import views

urlpatterns = [
    # 인증 API
    path('api/auth/register/', views.register, name='register'),
    path('api/auth/login/', views.login_view, name='login'),
    path('api/auth/logout/', views.logout_view, name='logout'),
    path('api/auth/user/', views.user_info, name='user_info'),
    path('api/auth/change-password/', views.change_password, name='change_password'),
    
    # 팀/워크스페이스 API
    path('api/teams/create/', views.create_team, name='create_team'),
    path('api/teams/', views.list_teams, name='list_teams'),
    path('api/teams/<str:team_id>/', views.get_team, name='get_team'),
    path('api/teams/<str:team_id>/invite/', views.invite_member, name='invite_member'),
    path('api/teams/<str:team_id>/members/<str:member_id>/role/', views.update_member_role, name='update_member_role'),
    path('api/teams/<str:team_id>/members/<str:member_id>/remove/', views.remove_member, name='remove_member'),
    path('api/teams/join/', views.join_team_by_code, name='join_team_by_code'),
    
    # AI 프롬프트 API (Pro 플랜 전용)
    path('api/ai/prompt/', views.ai_prompt, name='ai_prompt'),
    path('api/ai/usage/', views.ai_usage_stats, name='ai_usage_stats'),
    path('api/ai/usage/today/', views.ai_usage_today, name='ai_usage_today'),
]

