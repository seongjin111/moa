# 실행 가이드 (팀원 버전)

## 실행 방법

### 1. GitHub에서 dsh38 브랜치 받기
```bash
git checkout dsh38
# 또는
git pull origin dsh38
```

### 2. 프로젝트 폴더로 이동
```bash
cd moa-dsh38
```

### 3. 서버 실행

**macOS/Linux:**
```bash
python3 manage.py runserver
# 또는
python manage.py runserver
```

**Windows:**
```bash
py manage.py runserver
```

### 4. 브라우저에서 접속

**에디터:**
- http://127.0.0.1:8000 (또는 http://localhost:8000)
- ⚠️ **https가 아닌 http입니다!**

**관리자 패널:**
- http://127.0.0.1:8000/admin
- 아이디: `capd_admin@dsh38.com`
- 비밀번호: `capd_admin`

**관리 패널:**
- http://127.0.0.1:8000/adminpanel

### 5. 서버 종료
터미널에서 `Ctrl + C` 누르기

---

## 현재 작동하는 기능

✅ **정상 작동:**
- 에디터 기본 기능
- 저장/공유
- 열람
- 관리 패널 접속
- 삭제 기능

⚠️ **문제 있음:**
- 글꼴 선택 (수정 필요)
- 글꼴 크기 선택 (수정 필요)
- 관리 패널의 편집/히스토리 기능 (삭제됨)

---

## 주의사항

1. **URL 주소**: `https://`가 아닌 `http://`를 사용하세요
2. **명령어**: macOS/Linux에서는 `python3` 또는 `python` 사용
3. **포트**: 기본적으로 8000번 포트 사용

---

## 문제 해결

### 서버가 시작되지 않을 때
```bash
# 마이그레이션 확인
python3 manage.py showmigrations

# 마이그레이션 실행 (필요시)
python3 manage.py migrate
```

### 포트가 이미 사용 중일 때
```bash
# 다른 포트 사용
python3 manage.py runserver 8001
```

---

## 빠른 실행

```bash
# 1. 프로젝트 폴더로 이동
cd moa-dsh38

# 2. 서버 실행 (macOS)
python3 manage.py runserver

# 3. 브라우저에서 http://127.0.0.1:8000 접속
```


