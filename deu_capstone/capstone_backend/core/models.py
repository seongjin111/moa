from django.db import models
import uuid

class Memo(models.Model):
    # 비회원도 구분할 수 있는 고유 ID (URL 공유용)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200, default="제목 없음")
    content = models.TextField() # 드로잉 데이터(JSON)나 텍스트
    created_at = models.DateTimeField(auto_now_add=True)

    # 비밀번호를 걸 경우를 대비 (Null 허용)
    access_password = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.title