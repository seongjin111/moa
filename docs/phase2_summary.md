# Phase 2 구현 완료 요약 - 팀/워크스페이스 기능

## 구현 완료된 기능

### 1. 팀/워크스페이스 모델 설계 ✅

#### Team 모델
- UUID 기반 ID
- 팀 이름, 설명
- 소유자 (owner)
- 공개/비공개 설정
- 초대 코드 자동 생성 (10자리 Base62)
- 통계 (노트 수, 멤버 수)

#### TeamMember 모델
- 역할 관리: owner, admin, member, viewer
- 초대 정보 (invited_by)
- 활성/비활성 상태
- 역할별 권한 속성:
  - `can_edit_team`: 팀 설정 편집 (owner, admin)
  - `can_manage_members`: 멤버 관리 (owner, admin)
  - `can_create_note`: 노트 생성 (owner, admin, member)
  - `can_edit_note`: 노트 편집 (owner, admin, member)
  - `can_view_note`: 노트 조회 (모든 활성 멤버)

---

### 2. 팀 관리 API ✅

#### 팀 생성
- `POST /api/teams/create/`
- Body: `{ "name": "팀 이름", "description": "설명", "is_public": false }`
- 소유자를 자동으로 owner 역할로 추가

#### 팀 목록 조회
- `GET /api/teams/`
- 사용자가 속한 모든 팀 조회
- 역할 정보 포함

#### 팀 상세 정보
- `GET /api/teams/{team_id}/`
- 팀 정보 및 멤버 목록 조회
- 현재 사용자의 역할 정보 포함

#### 멤버 초대
- `POST /api/teams/{team_id}/invite/`
- Body: `{ "username": "사용자명" 또는 "email": "이메일", "role": "member" }`
- admin, member, viewer 역할 초대 가능
- owner 역할은 초대 불가 (자동 생성)

#### 초대 코드로 가입
- `POST /api/teams/join/`
- Body: `{ "invite_code": "초대 코드" }`
- 공개 팀만 가능

#### 멤버 역할 변경
- `POST /api/teams/{team_id}/members/{member_id}/role/`
- Body: `{ "role": "admin" | "member" | "viewer" }`
- 소유자만 가능

#### 멤버 제거
- `POST /api/teams/{team_id}/members/{member_id}/remove/`
- 자기 자신 제거 가능
- 소유자는 제거 불가

---

### 3. 팀별 노트 관리 ✅

#### Note 모델 확장
- `team` 필드 추가 (ForeignKey to Team)
- null이면 개인 노트, 값이 있으면 팀 노트
- 인덱스 추가: `team`, `-created_at`

#### 노트 저장 시 팀 지원
- `POST /save/`에 `team_id` 파라미터 추가
- 팀 노트 생성 시 권한 검증
- 팀 노트 수 자동 증가

#### 권한 검증
- `core/utils.py`에 권한 검증 함수 추가:
  - `can_create_note(user, team)`
  - `can_edit_note(user, note)`
  - `can_view_note(user, note)`

---

### 4. 관리자 페이지 ✅

#### Team Admin
- 목록: 이름, 소유자, 공개 여부, 멤버 수, 노트 수
- 필터: 공개 여부, 생성일
- 검색: 이름, 설명, 소유자, 초대 코드

#### TeamMember Admin
- 목록: 팀, 사용자, 역할, 활성 여부
- 필터: 역할, 활성 여부, 가입일
- 검색: 팀 이름, 사용자명, 이메일

---

## 데이터베이스 마이그레이션

### 생성된 마이그레이션 파일
- `core/migrations/0002_team_teammember.py` - Team, TeamMember 모델
- `notes/migrations/0002_note_team.py` - Note 모델에 team 필드 추가

### 마이그레이션 실행 방법
```bash
python manage.py migrate core
python manage.py migrate notes
```

---

## API 사용 예시

### 팀 생성
```bash
curl -X POST http://localhost:8000/api/teams/create/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=<session_id>" \
  -d '{
    "name": "개발팀",
    "description": "프로젝트 개발을 위한 팀",
    "is_public": false
  }'
```

### 팀 목록 조회
```bash
curl -X GET http://localhost:8000/api/teams/ \
  -H "Cookie: sessionid=<session_id>"
```

### 멤버 초대
```bash
curl -X POST http://localhost:8000/api/teams/{team_id}/invite/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=<session_id>" \
  -d '{
    "username": "newmember",
    "role": "member"
  }'
```

### 팀 노트 생성
```bash
curl -X POST http://localhost:8000/save/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Cookie: sessionid=<session_id>" \
  -d 'title=팀 노트&content_json={"type":"html","html":"<p>내용</p>"}&team_id={team_id}'
```

---

## 역할 및 권한

### Owner (소유자)
- 팀 설정 편집
- 멤버 관리 (초대, 제거, 역할 변경)
- 노트 생성/편집/조회
- 팀 삭제 (향후 구현)

### Admin (관리자)
- 멤버 관리 (초대, 제거, 역할 변경)
- 노트 생성/편집/조회
- 팀 설정 편집 불가

### Member (멤버)
- 노트 생성/편집/조회
- 멤버 관리 불가

### Viewer (뷰어)
- 노트 조회만 가능
- 노트 생성/편집 불가

---

## 다음 단계 (Phase 3)

1. **미디어 파일 확장**
   - 음성 파일 업로드 API
   - 영상 파일 업로드 API
   - 파일 타입별 검증 강화

2. **공유 기능 고도화**
   - QR 코드 생성
   - 공유 권한 세분화 (읽기/편집)

3. **플랜 관리**
   - 결제 연동
   - 플랜별 기능 제한 미들웨어

4. **AI 프롬프트 기능**
   - AI 서비스 연동
   - Pro 플랜 전용 기능

---

## 완료된 TODO

- ✅ Team 모델 설계 (워크스페이스)
- ✅ TeamMember 모델 설계 (역할: owner, admin, member, viewer)
- ✅ 팀 생성 API 구현
- ✅ 팀 멤버 초대 API 구현
- ✅ 팀 멤버 관리 API (추가/제거/역할 변경)
- ✅ 팀별 노트 관리 기능
- ✅ 권한 검증 미들웨어/유틸리티 함수
- ✅ Note 모델에 team 필드 추가


