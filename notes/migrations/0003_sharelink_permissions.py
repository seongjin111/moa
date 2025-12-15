# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0002_note_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharelink',
            name='permission',
            field=models.CharField(choices=[('read', '읽기 전용'), ('edit', '편집 가능')], default='read', help_text='공유 권한 (읽기 전용/편집 가능)', max_length=10),
        ),
        migrations.AddField(
            model_name='sharelink',
            name='view_password_hash',
            field=models.CharField(blank=True, help_text='열람 비밀번호 해시', max_length=128, null=True),
        ),
    ]


