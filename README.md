# Bano (바로 노트)

대학 과제용 웹 메모 서비스. OneNote 유사 자유 배치 에디터를 제공하며, 비회원 즉시 메모, 공유 링크 기반 읽기/편집 권한, 관리자 포털 및 IP별 일일 제한을 포함합니다.

## 핵심 기능
- TipTap 기반 자유 배치 리치 에디터(이미지 DnD, 유튜브 링크 재생)
- 저장/공유 버튼으로만 영속화(자동 저장 없음)
- 히스토리: 저장 시 스냅샷 생성 + HTML 디프 표시
- 공유 링크: 영문대소문자+숫자 10자리, 6개월 만료
- 편집 비밀번호: 설정/검증/변경(찾기 없음)
- IP별 하루 최대 10회 저장/공유 제한
- 세션 타임아웃 30분, 세션 만료 시 미저장 내용 폐기
- 관리자 포털: 노트 열람/편집/삭제(소프트), 공유/만료 관리, 감사 로그

## 저장소 설계(파일 기반, DB 마이그레이션 대비)
`data/` 루트 하에 다음 구조를 사용합니다:
- `notes/{note_id}/meta.json`
- `notes/{note_id}/content.json` (TipTap/Quill 유사 JSON 포맷)
- `notes/{note_id}/attachments/{file_id}` (이미지)
- `history/{history_id}.json` (스냅샷/HTML 디프)
- `shares/{token}.json` (10자리 토큰, 만료 6개월)
- `quota/{YYYYMMDD}/{ip}.json` (일일 카운트)
- `admin_logs/{YYYYMMDD}.log` (감사 로그)

마이그레이션 시 각 JSON 구조는 DB 스키마로 직렬화 가능합니다.

## 프로젝트 구조(계획)
- `bano/` Django 프로젝트
- 앱: `core/`, `notes/`, `sharing/`, `adminpanel/`
- 서비스: `core/services/storage.py`, `quota.py`, `history.py`, `permissions.py`
- 미들웨어: `client_token.py`
- 템플릿: 한국어 UI

## 개발 단계(MVP)
1) 에디터+저장/로드(세션 정책)  
2) 공유 링크/읽기/편집 비밀번호 검증  
3) 히스토리 스냅샷+HTML 디프 표시  
4) IP 제한/보안(해시/CSRF/이미지 검증/변환/Sanitization)  
5) 관리자 포털+감사 로그

## 실행(초기화 예정)
Windows PowerShell에서 가상환경/Django 설치 및 프로젝트 초기화를 진행합니다. 자세한 명령은 프로젝트 생성 후 업데이트됩니다.

## 설치 직후 해야할것
1. 
```
python -m venv venv
```

2.
```
./venv/Scripts/Activate.ps1

또는
ctrl shift p 
-> 
select python interpreter 
-> 
.\venv\Scripts\python.exe
```

보안 오류 뜨면
```
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
3.
```
pip install -r requirements.txt
```




