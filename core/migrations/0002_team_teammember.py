# Generated manually

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='팀 이름', max_length=200)),
                ('description', models.TextField(blank=True, help_text='팀 설명', max_length=1000, null=True)),
                ('is_public', models.BooleanField(default=False, help_text='공개 팀 여부 (초대 없이 가입 가능)')),
                ('invite_code', models.CharField(blank=True, help_text='초대 코드 (공개 팀용)', max_length=20, null=True, unique=True)),
                ('notes_count', models.IntegerField(default=0, help_text='팀 노트 수')),
                ('members_count', models.IntegerField(default=0, help_text='멤버 수')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(help_text='팀 소유자', on_delete=django.db.models.deletion.CASCADE, related_name='owned_teams', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '팀',
                'verbose_name_plural': '팀',
                'db_table': 'team',
            },
        ),
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('owner', '소유자'), ('admin', '관리자'), ('member', '멤버'), ('viewer', '뷰어')], default='member', help_text='팀 내 역할', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='활성 멤버 여부')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invited_by', models.ForeignKey(blank=True, help_text='초대한 사용자', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invited_members', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='core.team')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '팀 멤버',
                'verbose_name_plural': '팀 멤버',
                'db_table': 'team_member',
                'unique_together': {('team', 'user')},
            },
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['owner', '-created_at'], name='team_owner_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['invite_code'], name='team_invite_code_idx'),
        ),
        migrations.AddIndex(
            model_name='teammember',
            index=models.Index(fields=['team', 'role'], name='team_member_team_role_idx'),
        ),
        migrations.AddIndex(
            model_name='teammember',
            index=models.Index(fields=['user', '-joined_at'], name='team_member_user_joined_idx'),
        ),
    ]


