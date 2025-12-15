from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Team, TeamMember, AIPromptUsage


class UserProfileInline(admin.StackedInline):
    """User 관리 페이지에 UserProfile 인라인으로 표시"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = '프로필'


class UserAdmin(BaseUserAdmin):
    """User 관리자 페이지 확장"""
    inlines = (UserProfileInline,)


# 기존 UserAdmin 등록 해제 후 재등록
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# UserProfile 직접 관리
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'plan', 'email_verified', 'notes_count', 'created_at')
    list_filter = ('plan', 'email_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'display_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'members_count', 'notes_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description', 'owner__username', 'invite_code')
    readonly_fields = ('id', 'invite_code', 'members_count', 'notes_count', 'created_at', 'updated_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'name', 'description', 'owner')
        }),
        ('설정', {
            'fields': ('is_public', 'invite_code')
        }),
        ('통계', {
            'fields': ('members_count', 'notes_count')
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('team__name', 'user__username', 'user__email')
    readonly_fields = ('id', 'joined_at', 'updated_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'team', 'user', 'role')
        }),
        ('초대 정보', {
            'fields': ('invited_by',)
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('타임스탬프', {
            'fields': ('joined_at', 'updated_at')
        }),
    )


@admin.register(AIPromptUsage)
class AIPromptUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'model', 'tokens_used', 'cost', 'created_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('user__username', 'user__email', 'prompt')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'user', 'created_at')
        }),
        ('프롬프트', {
            'fields': ('prompt', 'response')
        }),
        ('AI 서비스', {
            'fields': ('provider', 'model')
        }),
        ('사용량', {
            'fields': ('tokens_used', 'cost')
        }),
    )
