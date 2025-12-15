from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class UserProfile(models.Model):
    """
    사용자 프로필 확장 모델
    Django 기본 User 모델과 One-to-One 관계
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 추가 정보
    display_name = models.CharField(max_length=100, blank=True, null=True, help_text="표시 이름")
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="자기소개")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, help_text="프로필 이미지")
    
    # 계정 설정
    email_verified = models.BooleanField(default=False, help_text="이메일 인증 여부")
    plan = models.CharField(
        max_length=20,
        choices=[('free', '무료'), ('pro', 'Pro')],
        default='free',
        help_text="사용자 플랜"
    )
    
    # 통계
    notes_count = models.IntegerField(default=0, help_text="생성한 노트 수")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필'
    
    def __str__(self):
        return f"{self.user.username}의 프로필"
    
    @property
    def is_pro(self):
        """Pro 플랜 여부 확인"""
        return self.plan == 'pro'


class AIPromptUsage(models.Model):
    """
    AI 프롬프트 사용량 추적 모델
    Pro 플랜 사용자의 AI 사용량 관리
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_prompt_usages')
    
    # 프롬프트 정보
    prompt = models.TextField(help_text="사용한 프롬프트")
    response = models.TextField(blank=True, null=True, help_text="AI 응답")
    
    # AI 서비스 정보
    provider = models.CharField(
        max_length=50,
        choices=[
            ('openai', 'OpenAI'),
            ('claude', 'Claude (Anthropic)'),
            ('gemini', 'Google Gemini'),
        ],
        default='openai',
        help_text="AI 서비스 제공자"
    )
    model = models.CharField(max_length=100, help_text="사용한 AI 모델")
    
    # 사용량 정보
    tokens_used = models.IntegerField(default=0, help_text="사용한 토큰 수")
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text="비용 (USD)")
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_prompt_usage'
        verbose_name = 'AI 프롬프트 사용량'
        verbose_name_plural = 'AI 프롬프트 사용량'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['provider', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.provider} - {self.created_at}"


class Team(models.Model):
    """
    팀/워크스페이스 모델
    여러 사용자가 협업할 수 있는 공간
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="팀 이름")
    description = models.TextField(max_length=1000, blank=True, null=True, help_text="팀 설명")
    
    # 소유자
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_teams',
        help_text="팀 소유자"
    )
    
    # 설정
    is_public = models.BooleanField(default=False, help_text="공개 팀 여부 (초대 없이 가입 가능)")
    invite_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="초대 코드 (공개 팀용)"
    )
    
    # 통계
    notes_count = models.IntegerField(default=0, help_text="팀 노트 수")
    members_count = models.IntegerField(default=0, help_text="멤버 수")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team'
        verbose_name = '팀'
        verbose_name_plural = '팀'
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['invite_code']),
        ]
    
    def __str__(self):
        return f"{self.name} (소유자: {self.owner.username})"
    
    def save(self, *args, **kwargs):
        """초대 코드 자동 생성"""
        if not self.invite_code:
            from core.services.storage import generate_share_token
            # 10자리 Base62 토큰 생성
            self.invite_code = generate_share_token()
        super().save(*args, **kwargs)


class TeamMember(models.Model):
    """
    팀 멤버 모델
    사용자와 팀의 관계 및 역할 관리
    """
    ROLE_CHOICES = [
        ('owner', '소유자'),
        ('admin', '관리자'),
        ('member', '멤버'),
        ('viewer', '뷰어'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    
    # 역할
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        help_text="팀 내 역할"
    )
    
    # 초대 정보
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_members',
        help_text="초대한 사용자"
    )
    
    # 상태
    is_active = models.BooleanField(default=True, help_text="활성 멤버 여부")
    
    # 타임스탬프
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team_member'
        verbose_name = '팀 멤버'
        verbose_name_plural = '팀 멤버'
        unique_together = [['team', 'user']]
        indexes = [
            models.Index(fields=['team', 'role']),
            models.Index(fields=['user', '-joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.get_role_display()})"
    
    @property
    def can_edit_team(self):
        """팀 설정 편집 권한"""
        return self.role in ('owner', 'admin')
    
    @property
    def can_manage_members(self):
        """멤버 관리 권한"""
        return self.role in ('owner', 'admin')
    
    @property
    def can_create_note(self):
        """노트 생성 권한"""
        return self.role in ('owner', 'admin', 'member')
    
    @property
    def can_edit_note(self):
        """노트 편집 권한"""
        return self.role in ('owner', 'admin', 'member')
    
    @property
    def can_view_note(self):
        """노트 조회 권한"""
        return self.is_active


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """User 생성 시 자동으로 UserProfile 생성"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """User 저장 시 UserProfile도 함께 저장"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=TeamMember)
def update_team_members_count(sender, instance, **kwargs):
    """팀 멤버 수 업데이트"""
    if instance.is_active:
        instance.team.members_count = TeamMember.objects.filter(
            team=instance.team,
            is_active=True
        ).count()
        instance.team.save(update_fields=['members_count'])
