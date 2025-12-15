# Generated manually

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0002_team_teammember'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIPromptUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('prompt', models.TextField(help_text='사용한 프롬프트')),
                ('response', models.TextField(blank=True, help_text='AI 응답', null=True)),
                ('provider', models.CharField(choices=[('openai', 'OpenAI'), ('claude', 'Claude (Anthropic)'), ('gemini', 'Google Gemini')], default='openai', help_text='AI 서비스 제공자', max_length=50)),
                ('model', models.CharField(help_text='사용한 AI 모델', max_length=100)),
                ('tokens_used', models.IntegerField(default=0, help_text='사용한 토큰 수')),
                ('cost', models.DecimalField(decimal_places=6, default=0, help_text='비용 (USD)', max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_prompt_usages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'AI 프롬프트 사용량',
                'verbose_name_plural': 'AI 프롬프트 사용량',
                'db_table': 'ai_prompt_usage',
            },
        ),
        migrations.AddIndex(
            model_name='aipromptusage',
            index=models.Index(fields=['user', '-created_at'], name='ai_prompt_u_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='aipromptusage',
            index=models.Index(fields=['provider', '-created_at'], name='ai_prompt_u_provider_idx'),
        ),
    ]


