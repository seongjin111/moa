# Generated manually

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(blank=True, help_text='표시 이름', max_length=100, null=True)),
                ('bio', models.TextField(blank=True, help_text='자기소개', max_length=500, null=True)),
                ('avatar', models.ImageField(blank=True, help_text='프로필 이미지', null=True, upload_to='avatars/')),
                ('email_verified', models.BooleanField(default=False, help_text='이메일 인증 여부')),
                ('plan', models.CharField(choices=[('free', '무료'), ('pro', 'Pro')], default='free', help_text='사용자 플랜', max_length=20)),
                ('notes_count', models.IntegerField(default=0, help_text='생성한 노트 수')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '사용자 프로필',
                'verbose_name_plural': '사용자 프로필',
                'db_table': 'user_profile',
            },
        ),
    ]


