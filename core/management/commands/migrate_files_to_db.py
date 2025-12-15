"""
파일 기반 저장소를 DB로 마이그레이션하는 명령어

사용법:
    python manage.py migrate_files_to_db

주의사항:
    - 기존 파일 데이터는 유지됩니다
    - 중복 실행 시 중복 데이터가 생성될 수 있습니다
    - 마이그레이션 전 백업을 권장합니다
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import json
from datetime import datetime
from django.utils import timezone

from notes.models import Note, NoteHistory, ShareLink
from core.services import storage


class Command(BaseCommand):
    help = '파일 기반 저장소를 DB로 마이그레이션'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 마이그레이션하지 않고 시뮬레이션만 실행',
        )
        parser.add_argument(
            '--skip-shares',
            action='store_true',
            help='공유 링크 마이그레이션 건너뛰기',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_shares = options['skip_shares']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드: 실제로 마이그레이션하지 않습니다.'))
        
        # 노트 마이그레이션
        self.stdout.write('노트 마이그레이션 시작...')
        notes_migrated = self.migrate_notes(dry_run)
        self.stdout.write(self.style.SUCCESS(f'{notes_migrated}개의 노트가 마이그레이션되었습니다.'))
        
        # 공유 링크 마이그레이션
        if not skip_shares:
            self.stdout.write('공유 링크 마이그레이션 시작...')
            shares_migrated = self.migrate_shares(dry_run)
            self.stdout.write(self.style.SUCCESS(f'{shares_migrated}개의 공유 링크가 마이그레이션되었습니다.'))
        else:
            self.stdout.write(self.style.WARNING('공유 링크 마이그레이션을 건너뜁니다.'))
        
        self.stdout.write(self.style.SUCCESS('마이그레이션이 완료되었습니다!'))

    def migrate_notes(self, dry_run=False):
        """노트 파일을 DB로 마이그레이션"""
        notes_dir = Path(settings.DATA_ROOT) / 'notes'
        if not notes_dir.exists():
            self.stdout.write(self.style.WARNING('노트 디렉토리가 없습니다.'))
            return 0
        
        migrated_count = 0
        skipped_count = 0
        
        for note_dir in notes_dir.iterdir():
            if not note_dir.is_dir():
                continue
            
            note_id = note_dir.name
            
            # 이미 DB에 존재하는지 확인
            try:
                Note.objects.get(id=note_id)
                skipped_count += 1
                self.stdout.write(f'노트 {note_id}는 이미 DB에 존재합니다. 건너뜁니다.')
                continue
            except Note.DoesNotExist:
                pass
            
            # 메타데이터 읽기
            meta_path = note_dir / 'meta.json'
            content_path = note_dir / 'content.json'
            
            if not meta_path.exists() or not content_path.exists():
                self.stdout.write(self.style.WARNING(f'노트 {note_id}의 필수 파일이 없습니다. 건너뜁니다.'))
                continue
            
            try:
                meta = storage.read_json(meta_path)
                content = storage.read_json(content_path)
                
                if not meta:
                    continue
                
                # 날짜 파싱
                created_at = self.parse_datetime(meta.get('created_at'))
                updated_at = self.parse_datetime(meta.get('updated_at'))
                
                if not dry_run:
                    # Note 생성
                    note = Note.objects.create(
                        id=note_id,
                        title=meta.get('title', '제목 없음'),
                        content_json=content or {},
                        creator_client_token=meta.get('creator_client_token'),
                        creator_ip=meta.get('creator_ip'),
                        status=meta.get('status', 'active'),
                        edit_password_hash=meta.get('edit_password_hash'),
                        created_at=created_at or timezone.now(),
                        updated_at=updated_at or timezone.now()
                    )
                    
                    # 히스토리 마이그레이션
                    history_ids = meta.get('history_ids', [])
                    for history_id in history_ids:
                        self.migrate_history(history_id, note, dry_run)
                    
                    migrated_count += 1
                    self.stdout.write(f'노트 {note_id} 마이그레이션 완료')
                else:
                    migrated_count += 1
                    self.stdout.write(f'[DRY RUN] 노트 {note_id} 마이그레이션 예정')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'노트 {note_id} 마이그레이션 실패: {str(e)}'))
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'{skipped_count}개의 노트가 건너뛰어졌습니다.'))
        
        return migrated_count

    def migrate_history(self, history_id, note, dry_run=False):
        """히스토리 파일을 DB로 마이그레이션"""
        history_path = storage.history_path(history_id)
        if not history_path.exists():
            return
        
        try:
            hist_data = storage.read_json(history_path)
            if not hist_data:
                return
            
            if hist_data.get('note_id') != str(note.id):
                return
            
            if not dry_run:
                # NoteHistory 생성
                NoteHistory.objects.get_or_create(
                    id=history_id,
                    defaults={
                        'note': note,
                        'before_html': hist_data.get('before_html', ''),
                        'after_html': hist_data.get('after_html', ''),
                        'diff_html': hist_data.get('diff_html', ''),
                        'editor_session_id': hist_data.get('editor_session_id', ''),
                        'created_at': self.parse_datetime(hist_data.get('timestamp')) or timezone.now()
                    }
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'히스토리 {history_id} 마이그레이션 실패: {str(e)}'))

    def migrate_shares(self, dry_run=False):
        """공유 링크 파일을 DB로 마이그레이션"""
        shares_dir = Path(settings.DATA_ROOT) / 'shares'
        if not shares_dir.exists():
            self.stdout.write(self.style.WARNING('공유 링크 디렉토리가 없습니다.'))
            return 0
        
        migrated_count = 0
        skipped_count = 0
        
        for share_file in shares_dir.glob('*.json'):
            token = share_file.stem
            
            # 이미 DB에 존재하는지 확인
            try:
                ShareLink.objects.get(token=token)
                skipped_count += 1
                self.stdout.write(f'공유 링크 {token}는 이미 DB에 존재합니다. 건너뜁니다.')
                continue
            except ShareLink.DoesNotExist:
                pass
            
            try:
                data = storage.read_json(share_file)
                if not data:
                    continue
                
                # 노트 확인
                note_id = data.get('note_id')
                if not note_id:
                    continue
                
                try:
                    note = Note.objects.get(id=note_id)
                except Note.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'공유 링크 {token}의 노트 {note_id}가 DB에 없습니다. 건너뜁니다.'))
                    continue
                
                # 날짜 파싱
                created_at = self.parse_datetime(data.get('created_at'))
                expires_at = self.parse_datetime(data.get('expires_at'))
                
                if not expires_at:
                    expires_at = (created_at or timezone.now()) + timedelta(days=180)
                
                if not dry_run:
                    # ShareLink 생성
                    ShareLink.objects.create(
                        token=token,
                        note=note,
                        edit_password_hash=data.get('edit_password_hash'),
                        active=data.get('active', True),
                        expires_at=expires_at,
                        created_at=created_at or timezone.now()
                    )
                    
                    migrated_count += 1
                    self.stdout.write(f'공유 링크 {token} 마이그레이션 완료')
                else:
                    migrated_count += 1
                    self.stdout.write(f'[DRY RUN] 공유 링크 {token} 마이그레이션 예정')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'공유 링크 {token} 마이그레이션 실패: {str(e)}'))
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'{skipped_count}개의 공유 링크가 건너뛰어졌습니다.'))
        
        return migrated_count

    def parse_datetime(self, dt_str):
        """ISO 형식 날짜 문자열을 datetime 객체로 변환"""
        if not dt_str:
            return None
        
        try:
            # ISO 형식 파싱
            if 'T' in dt_str:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(dt_str)
            
            # timezone aware로 변환
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            
            return dt
        except Exception:
            return None

