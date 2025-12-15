# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_team_teammember'),
        ('notes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='team',
            field=models.ForeignKey(blank=True, help_text='소속 팀 (null이면 개인 노트)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notes', to='core.team'),
        ),
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['team', '-created_at'], name='note_team_created_idx'),
        ),
    ]


