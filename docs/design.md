# Bano 설계 문서

## 요구사항 확정 요약
- TipTap + 커스텀 노드/포지셔닝(OneNote 유사 자유 배치)
- 이미지 첨부만 허용(최대 10MB), 동영상 불가. 유튜브 링크 임베드 지원.
- 저장 버튼 시 스냅샷 생성, 히스토리는 HTML 디프로 표시
- 공유 링크 10자리(Base62), 중복 검사, 6개월 만료
- 세션 타임아웃 30분, 세션 만료/새로고침 시 미저장 내용 폐기
- 관리자 감사 로그 필요
- 파일 기반 저장(향후 DB 이행 대비)

## 파일 저장 구조
```
data/
  notes/{note_id}/
    meta.json
    content.json
    attachments/{file_id}
  history/{history_id}.json
  shares/{token}.json
  quota/{YYYYMMDD}/{ip}.json
  admin_logs/{YYYYMMDD}.log
  index/
    notes_by_date.json
    shares_active.json
```

### meta.json
```
{
  "note_id": "abcdef0123456789",
  "title": "제목",
  "created_at": "2025-12-09T12:34:56Z",
  "updated_at": "2025-12-09T12:40:00Z",
  "creator_client_token": "<128bit base62>",
  "creator_ip": "203.0.113.1",
  "status": "active|expired|deleted",
  "history_ids": ["uuid-..."],
  "edit_password_hash": "argon2id$..."
}
```

### content.json
TipTap 문서 JSON. 서버 저장 전 Sanitization 처리.

### history/{history_id}.json
```
{
  "note_id": "abcdef0123456789",
  "timestamp": "2025-12-09T12:40:00Z",
  "before_html": "<...>",
  "after_html": "<...>",
  "diff_html": "<ins>...</ins><del>...</del>",
  "editor_session_id": "session-..."
}
```

### shares/{token}.json
```
{
  "note_id": "abcdef0123456789",
  "token": "dT38T3sTYS",
  "created_at": "2025-12-09T12:45:00Z",
  "expires_at": "2026-06-09T12:45:00Z",
  "active": true,
  "edit_password_hash": "argon2id$..."
}
```

## 보안/권한
- 세션 쿠키 `client_token` 발급(비회원 임시 소유권)
- 편집 비밀번호 성공 시 `edit_session:{note_id}` 부여
- 비밀번호 해싱: Argon2(우선) 또는 PBKDF2
- CSRF: POST 보호
- XSS: 서버/클라이언트 Sanitization
- 링크 토큰: Base62 10자리, 고Entropy + 중복 검사

## 이미지 검증/변환
- 허용 MIME: `image/png`, `image/jpeg`, `image/webp`
- 최대 크기: 10MB
- 서버 변환: 너무 큰 해상도 리사이즈(webp 변환 옵션), 메타 제거, 위험한 SVG 금지

## IP 제한
- `quota/{YYYYMMDD}/{ip}.json` 카운트: 저장1, 공유1 포함 일일 합계 10
- 파일락으로 경합 완화

## 관리자 포털
- Django 인증 + 관리자 테이블
- 목록/검색, 상세/편집, 공유 관리, 만료/삭제(소프트), 감사 로그

## 마이그레이션 대비
- 모든 JSON 구조는 DB 스키마로 직렬화 가능(문서 JSON은 JSONB 등)
- 파일 경로는 객체 스토리지로 대체 가능

## 프로젝트 초기 스캐폴딩 계획
- `bano` Django 프로젝트 생성
- 앱: `core`, `notes`, `sharing`, `adminpanel`
- 미들웨어: `client_token`
- 서비스: `storage`, `quota`, `history`, `permissions`
- 라우팅: 작성/저장, 읽기(`/s/{token}`), 편집 비밀번호 검증, 공유 생성
- 에디터: TipTap 초기화 및 업로드 엔드포인트
