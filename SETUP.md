# 실행 가이드

## 현재 상태

✅ **코드 구현 완료**: 모든 백엔드 기능이 구현되었습니다.
⚠️ **실행 전 준비 필요**: 아래 단계를 따라 실행 환경을 준비해야 합니다.

---

## 실행 전 준비 사항

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- Django>=6.0
- Pillow>=10.0.0
- bleach>=6.0.0
- qrcode[pil]>=7.4.2
- openai>=1.0.0 (AI 기능 사용 시)
- anthropic>=0.18.0 (AI 기능 사용 시)

### 3. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
python manage.py migrate core
python manage.py migrate notes

# 관리자 계정 생성 (선택사항)
python manage.py createsuperuser
```

### 4. 필수 디렉토리 생성

```bash
# 미디어 파일 디렉토리
mkdir -p media/uploads
mkdir -p media/media/audio
mkdir -p media/media/video
mkdir -p media/avatars

# 파일 기반 저장소 디렉토리 (기존 기능용)
mkdir -p data/notes
mkdir -p data/history
mkdir -p data/shares
mkdir -p data/quota
mkdir -p data/admin_logs
mkdir -p data/index
```

### 5. 환경 변수 설정 (선택사항)

AI 기능을 사용하려면:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

또는 `.env` 파일 사용 (python-decouple 등 사용)

---

## 실행 방법

### 개발 서버 실행

```bash
python manage.py runserver
```

기본적으로 `http://127.0.0.1:8000/`에서 실행됩니다.

### 정적 파일 수집 (프로덕션)

```bash
python manage.py collectstatic
```

---

## 실행 확인

### 1. 서버가 정상적으로 시작되는지 확인

```bash
python manage.py runserver
```

에러 없이 서버가 시작되면 성공입니다.

### 2. 기본 엔드포인트 확인

- `http://localhost:8000/` - 에디터 페이지
- `http://localhost:8000/admin/` - 관리자 페이지
- `http://localhost:8000/api/auth/register/` - 회원가입 API

### 3. API 테스트

```bash
# 회원가입 테스트
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"test1234"}'
```

---

## 문제 해결

### 마이그레이션 오류

```bash
# 마이그레이션 파일 확인
python manage.py showmigrations

# 특정 앱만 마이그레이션
python manage.py migrate core
python manage.py migrate notes
```

### Import 오류

```bash
# 의존성 재설치
pip install -r requirements.txt --upgrade
```

### 미디어 파일 업로드 오류

- `MEDIA_ROOT` 디렉토리가 존재하는지 확인
- 디렉토리 권한 확인 (쓰기 권한 필요)

### AI 기능 오류

- API 키가 설정되었는지 확인
- `openai` 또는 `anthropic` 라이브러리가 설치되었는지 확인

---

## 현재 코드 상태

✅ **구현 완료된 기능**:
- 회원 관리 시스템
- 팀/워크스페이스 기능
- 노트 생성/편집/히스토리
- 미디어 파일 업로드 (이미지/음성/영상)
- 공유 링크 및 QR 코드
- AI 프롬프트 기능 (Pro 플랜)

✅ **코드 품질**:
- 문법 오류 없음
- Linter 오류 없음
- 모든 import 정상

⚠️ **실행 전 필요**:
- Django 및 의존성 설치
- 데이터베이스 마이그레이션
- 필수 디렉토리 생성

---

## 빠른 시작

```bash
# 1. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는 venv\Scripts\activate  # Windows

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 마이그레이션 실행
python manage.py migrate

# 4. 서버 실행
python manage.py runserver
```

이제 `http://127.0.0.1:8000/`에서 서비스를 사용할 수 있습니다!


