# Generated manually

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(default='제목 없음', help_text='노트 제목', max_length=200)),
                ('content_json', models.JSONField(default=dict, help_text='TipTap 문서 JSON')),
                ('creator_client_token', models.CharField(blank=True, help_text='비회원 소유자 토큰', max_length=64, null=True)),
                ('creator_ip', models.GenericIPAddressField(blank=True, help_text='생성자 IP', null=True)),
                ('status', models.CharField(choices=[('active', '활성'), ('expired', '만료'), ('deleted', '삭제됨')], default='active', help_text='노트 상태', max_length=20)),
                ('edit_password_hash', models.CharField(blank=True, help_text='편집 비밀번호 해시', max_length=128, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, help_text='회원 소유자 (null이면 비회원)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '노트',
                'verbose_name_plural': '노트',
                'db_table': 'note',
            },
        ),
        migrations.CreateModel(
            name='ShareLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, help_text='10자리 Base62 토큰', max_length=10, unique=True)),
                ('edit_password_hash', models.CharField(blank=True, help_text='편집 비밀번호 해시', max_length=128, null=True)),
                ('active', models.BooleanField(default=True, help_text='활성 여부')),
                ('expires_at', models.DateTimeField(help_text='만료 시간 (6개월)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='share_links', to='notes.note')),
            ],
            options={
                'verbose_name': '공유 링크',
                'verbose_name_plural': '공유 링크',
                'db_table': 'share_link',
            },
        ),
        migrations.CreateModel(
            name='NoteHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('before_html', models.TextField(blank=True, help_text='변경 전 HTML')),
                ('after_html', models.TextField(blank=True, help_text='변경 후 HTML')),
                ('diff_html', models.TextField(blank=True, help_text='HTML 디프')),
                ('editor_session_id', models.CharField(blank=True, help_text='에디터 세션 ID', max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='histories', to='notes.note')),
            ],
            options={
                'verbose_name': '노트 히스토리',
                'verbose_name_plural': '노트 히스토리',
                'db_table': 'note_history',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MediaFile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(help_text='업로드된 파일', upload_to='media/%Y/%m/%d/')),
                ('file_type', models.CharField(choices=[('image', '이미지'), ('audio', '음성'), ('video', '영상')], help_text='파일 타입', max_length=20)),
                ('mime_type', models.CharField(help_text='MIME 타입', max_length=100)),
                ('file_size', models.BigIntegerField(help_text='파일 크기 (bytes)')),
                ('uploader_client_token', models.CharField(blank=True, help_text='업로더 (비회원 토큰)', max_length=64, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploader', models.ForeignKey(blank=True, help_text='업로더 (회원)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_files', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '미디어 파일',
                'verbose_name_plural': '미디어 파일',
                'db_table': 'media_file',
            },
        ),
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['owner', '-created_at'], name='note_owner_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['creator_client_token', '-created_at'], name='note_client__idx'),
        ),
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['status', '-updated_at'], name='note_status__idx'),
        ),
        migrations.AddIndex(
            model_name='notehistory',
            index=models.Index(fields=['note', '-created_at'], name='note_histor_note_id_idx'),
        ),
        migrations.AddIndex(
            model_name='sharelink',
            index=models.Index(fields=['token'], name='share_link_token_idx'),
        ),
        migrations.AddIndex(
            model_name='sharelink',
            index=models.Index(fields=['active', 'expires_at'], name='share_link_active_idx'),
        ),
        migrations.AddIndex(
            model_name='mediafile',
            index=models.Index(fields=['uploader', '-created_at'], name='media_file_upload_idx'),
        ),
        migrations.AddIndex(
            model_name='mediafile',
            index=models.Index(fields=['file_type', '-created_at'], name='media_file_type_idx'),
        ),
    ]


