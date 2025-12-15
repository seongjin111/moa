# Django 마이그레이션 가이드

## 마이그레이션이란?

**마이그레이션(Migration)**은 Django에서 데이터베이스 스키마(테이블 구조)를 관리하는 방법입니다.

### 간단히 말하면:
- **모델 코드** (Python 파일의 `models.py`)를 작성하면
- **마이그레이션 파일**이 생성되고
- 이를 실행하면 **데이터베이스에 실제 테이블**이 만들어집니다

### 예시:
```python
# models.py에 작성한 코드
class UserProfile(models.Model):
    user = models.OneToOneField(User, ...)
    plan = models.CharField(max_length=20, ...)
```

↓ 마이그레이션 실행 ↓

```sql
-- 데이터베이스에 실제로 생성되는 테이블
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    plan VARCHAR(20),
    ...
);
```

---

## 왜 필요한가요?

1. **모델 코드 → 데이터베이스 테이블 변환**
   - Python 코드로 작성한 모델을 실제 데이터베이스 테이블로 만들어줍니다

2. **데이터베이스 버전 관리**
   - 모델이 변경될 때마다 마이그레이션 파일이 생성되어 변경 이력을 추적할 수 있습니다

3. **팀 협업**
   - 다른 개발자도 같은 데이터베이스 구조를 만들 수 있습니다

---

## 현재 프로젝트의 마이그레이션 파일

### Core 앱 마이그레이션
- `0001_initial.py` - UserProfile 모델 생성
- `0002_team_teammember.py` - Team, TeamMember 모델 생성
- `0003_ai_prompt_usage.py` - AIPromptUsage 모델 생성

### Notes 앱 마이그레이션
- `0001_initial.py` - Note, NoteHistory, ShareLink, MediaFile 모델 생성
- `0002_note_team.py` - Note 모델에 team 필드 추가
- `0003_sharelink_permissions.py` - ShareLink 모델에 권한 필드 추가

---

## 마이그레이션 실행 방법

### 1. 마이그레이션 파일 생성 (이미 완료됨)
```bash
python manage.py makemigrations
```
→ 이미 마이그레이션 파일들이 생성되어 있으므로 이 단계는 건너뛰어도 됩니다.

### 2. 마이그레이션 실행 (필수!)
```bash
# 모든 앱의 마이그레이션 실행
python manage.py migrate

# 또는 특정 앱만 실행
python manage.py migrate core
python manage.py migrate notes
```

### 3. 실행 결과
- 데이터베이스(`db.sqlite3`)에 테이블이 생성됩니다
- `django_migrations` 테이블에 실행 기록이 저장됩니다

---

## 마이그레이션 실행 전후 비교

### 실행 전
```
db.sqlite3 (비어있거나 기본 테이블만 있음)
```

### 실행 후
```
db.sqlite3
├── django_migrations (마이그레이션 기록)
├── user_profile (UserProfile 모델)
├── team (Team 모델)
├── team_member (TeamMember 모델)
├── ai_prompt_usage (AIPromptUsage 모델)
├── note (Note 모델)
├── note_history (NoteHistory 모델)
├── share_link (ShareLink 모델)
└── media_file (MediaFile 모델)
```

---

## 마이그레이션 명령어

### 마이그레이션 상태 확인
```bash
python manage.py showmigrations
```
→ 어떤 마이그레이션이 실행되었는지 확인

### 마이그레이션 실행
```bash
python manage.py migrate
```
→ 모든 마이그레이션 실행

### 특정 마이그레이션으로 되돌리기
```bash
python manage.py migrate core 0001
```
→ core 앱을 0001 마이그레이션 상태로 되돌림

---

## 주의사항

1. **마이그레이션은 한 번만 실행**
   - 같은 마이그레이션을 여러 번 실행해도 안전합니다 (이미 실행된 것은 건너뜀)

2. **데이터 손실 가능성**
   - 모델을 삭제하거나 필드를 삭제하면 데이터가 손실될 수 있습니다
   - 프로덕션 환경에서는 백업 후 실행하세요

3. **순서 중요**
   - 마이그레이션은 순서대로 실행됩니다 (0001 → 0002 → 0003)

---

## 현재 프로젝트에서 실행해야 할 마이그레이션

```bash
# 1. Core 앱 마이그레이션
python manage.py migrate core

# 2. Notes 앱 마이그레이션  
python manage.py migrate notes

# 3. Django 기본 마이그레이션 (admin, auth 등)
python manage.py migrate
```

또는 한 번에:
```bash
python manage.py migrate
```

---

## 마이그레이션 실행 확인

### 방법 1: showmigrations 명령어
```bash
python manage.py showmigrations
```

출력 예시:
```
core
 [X] 0001_initial
 [X] 0002_team_teammember
 [X] 0003_ai_prompt_usage
notes
 [X] 0001_initial
 [X] 0002_note_team
 [X] 0003_sharelink_permissions
```

`[X]` 표시가 있으면 실행 완료, `[ ]` 표시가 있으면 미실행입니다.

### 방법 2: 데이터베이스 확인
```bash
python manage.py dbshell
sqlite> .tables
```

테이블 목록이 보이면 마이그레이션이 실행된 것입니다.

---

## 요약

**마이그레이션 = 모델 코드를 데이터베이스 테이블로 변환하는 과정**

1. 모델 코드 작성 ✅ (완료)
2. 마이그레이션 파일 생성 ✅ (완료)
3. 마이그레이션 실행 ⚠️ (필요)
4. 서버 실행 ✅

**지금 해야 할 일**: `python manage.py migrate` 실행!


