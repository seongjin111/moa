from django.db import models
from django.contrib.auth.models import User
import uuid


class Note(models.Model):
    """
    노트 모델
    기존 파일 기반 저장소 구조를 DB로 마이그레이션
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 기본 정보
    title = models.CharField(max_length=200, default='제목 없음', help_text="노트 제목")
    content_json = models.JSONField(default=dict, help_text="TipTap 문서 JSON")
    
    # 소유자 정보 (회원 또는 비회원)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes',
        help_text="회원 소유자 (null이면 비회원)"
    )
    creator_client_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="비회원 소유자 토큰"
    )
    creator_ip = models.GenericIPAddressField(null=True, blank=True, help_text="생성자 IP")
    
    # 상태 관리
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', '활성'),
            ('expired', '만료'),
            ('deleted', '삭제됨')
        ],
        default='active',
        help_text="노트 상태"
    )
    
    # 편집 비밀번호 (비회원 노트용)
    edit_password_hash = models.CharField(max_length=128, null=True, blank=True, help_text="편집 비밀번호 해시")
    
    # 팀/워크스페이스 (선택사항)
    team = models.ForeignKey(
        'core.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes',
        help_text="소속 팀 (null이면 개인 노트)"
    )
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'note'
        verbose_name = '노트'
        verbose_name_plural = '노트'
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['creator_client_token', '-created_at']),
            models.Index(fields=['status', '-updated_at']),
            models.Index(fields=['team', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.id})"
    
    @property
    def is_owned_by_user(self):
        """회원 소유 여부"""
        return self.owner is not None
    
    def can_edit(self, user=None, client_token=None, edit_session=False):
        """
        편집 권한 확인
        - 회원: owner와 일치하면 True
        - 비회원: client_token이 일치하면 True
        - 편집 세션이 있으면 True
        """
        if edit_session:
            return True
        if user and self.owner == user:
            return True
        if client_token and self.creator_client_token == client_token:
            return True
        return False


class NoteHistory(models.Model):
    """
    노트 히스토리 모델
    저장 시 스냅샷 생성
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='histories')
    
    # 변경 내용
    before_html = models.TextField(blank=True, help_text="변경 전 HTML")
    after_html = models.TextField(blank=True, help_text="변경 후 HTML")
    diff_html = models.TextField(blank=True, help_text="HTML 디프")
    
    # 메타데이터
    editor_session_id = models.CharField(max_length=128, blank=True, help_text="에디터 세션 ID")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'note_history'
        verbose_name = '노트 히스토리'
        verbose_name_plural = '노트 히스토리'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['note', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.note.title} - {self.created_at}"


class ShareLink(models.Model):
    """
    공유 링크 모델
    기존 파일 기반 shares/{token}.json 구조 반영
    """
    PERMISSION_CHOICES = [
        ('read', '읽기 전용'),
        ('edit', '편집 가능'),
    ]
    
    token = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="10자리 Base62 토큰"
    )
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='share_links')
    
    # 권한 설정
    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
        default='read',
        help_text="공유 권한 (읽기 전용/편집 가능)"
    )
    edit_password_hash = models.CharField(max_length=128, null=True, blank=True, help_text="편집 비밀번호 해시")
    view_password_hash = models.CharField(max_length=128, null=True, blank=True, help_text="열람 비밀번호 해시")
    
    # 상태 관리
    active = models.BooleanField(default=True, help_text="활성 여부")
    expires_at = models.DateTimeField(help_text="만료 시간 (6개월)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'share_link'
        verbose_name = '공유 링크'
        verbose_name_plural = '공유 링크'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['active', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.note.title} - {self.token}"
    
    @property
    def is_expired(self):
        """만료 여부 확인"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_active(self):
        """활성 상태 확인 (만료 포함)"""
        return self.active and not self.is_expired
    
    def can_edit(self, has_edit_session=False):
        """편집 권한 확인"""
        if self.permission == 'read':
            return False
        if has_edit_session:
            return True
        return self.permission == 'edit' and not self.edit_password_hash


class MediaFile(models.Model):
    """
    미디어 파일 모델
    이미지, 음성, 영상 파일 관리
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 파일 정보
    file = models.FileField(upload_to='media/%Y/%m/%d/', help_text="업로드된 파일")
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('image', '이미지'),
            ('audio', '음성'),
            ('video', '영상')
        ],
        help_text="파일 타입"
    )
    mime_type = models.CharField(max_length=100, help_text="MIME 타입")
    file_size = models.BigIntegerField(help_text="파일 크기 (bytes)")
    
    # 소유자 정보
    uploader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files',
        help_text="업로더 (회원)"
    )
    uploader_client_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="업로더 (비회원 토큰)"
    )
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'media_file'
        verbose_name = '미디어 파일'
        verbose_name_plural = '미디어 파일'
        indexes = [
            models.Index(fields=['uploader', '-created_at']),
            models.Index(fields=['file_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.file_type} - {self.file.name}"
