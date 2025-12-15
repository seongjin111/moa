# Phase 4 구현 완료 요약 - 공유 기능 고도화

## 구현 완료된 기능

### 1. 공유 권한 세분화 ✅

#### ShareLink 모델 확장
- **permission 필드 추가**: `read` (읽기 전용) 또는 `edit` (편집 가능)
- **view_password_hash 필드 추가**: 열람 비밀번호 지원
- **can_edit() 메서드**: 편집 권한 확인 로직

#### 권한 종류
- **read (읽기 전용)**: 노트 조회만 가능, 편집 불가
- **edit (편집 가능)**: 노트 조회 및 편집 가능

---

### 2. 공유 링크 생성 개선 ✅

#### `create_share` API 개선
- `permission` 파라미터 추가 (기본값: 'read')
- `view_password` 파라미터 추가 (열람 비밀번호)
- `edit_password` 파라미터 유지 (편집 비밀번호)

#### 요청 예시
```bash
curl -X POST http://localhost:8000/s/create/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Cookie: sessionid=<session_id>" \
  -d "note_id={note_id}&permission=edit&view_password=view123&edit_password=edit123"
```

#### 응답 예시
```json
{
  "success": true,
  "token": "dT38T3sTYS",
  "url": "http://localhost:8000/s/dT38T3sTYS/",
  "permission": "edit",
  "expires_at": "2025-07-01T12:00:00Z"
}
```

---

### 3. 공유 링크 조회 개선 ✅

#### `view_share` 함수 개선
- 열람 비밀번호 검증 추가
- 권한에 따른 편집 가능 여부 확인
- 읽기 전용 링크는 편집 불가

#### 동작 방식
1. 열람 비밀번호가 있으면 검증
2. 비밀번호가 맞으면 노트 내용 표시
3. 권한에 따라 편집 버튼 표시/숨김

---

### 4. QR 코드 생성 API ✅

#### 엔드포인트
- `GET /api/shares/{token}/qr/`

#### 기능
- 공유 링크 URL을 QR 코드로 변환
- SVG 형식으로 반환
- Base64 인코딩 옵션 제공

#### 요청 예시
```bash
curl -X GET http://localhost:8000/api/shares/dT38T3sTYS/qr/
```

#### 응답 예시
```json
{
  "success": true,
  "url": "http://localhost:8000/s/dT38T3sTYS/",
  "qr_code_svg": "<svg>...</svg>",
  "qr_code_base64": "PHN2Zz4uLi48L3N2Zz4=",
  "token": "dT38T3sTYS"
}
```

#### 사용 예시
```javascript
// QR 코드 생성
const response = await fetch(`/api/shares/${token}/qr/`);
const data = await response.json();

// SVG를 직접 표시
document.getElementById('qr-code').innerHTML = data.qr_code_svg;

// 또는 Base64 이미지로 표시
const img = document.createElement('img');
img.src = `data:image/svg+xml;base64,${data.qr_code_base64}`;
```

---

### 5. 공유 링크 정보 조회 API ✅

#### 엔드포인트
- `GET /api/shares/{token}/info/`

#### 기능
- 공유 링크의 상세 정보 조회
- 권한, 비밀번호 설정 여부, 만료 시간 등

#### 요청 예시
```bash
curl -X GET http://localhost:8000/api/shares/dT38T3sTYS/info/
```

#### 응답 예시
```json
{
  "success": true,
  "token": "dT38T3sTYS",
  "url": "http://localhost:8000/s/dT38T3sTYS/",
  "permission": "edit",
  "permission_display": "편집 가능",
  "has_edit_password": true,
  "has_view_password": false,
  "expires_at": "2025-07-01T12:00:00Z",
  "created_at": "2025-01-01T12:00:00Z",
  "note": {
    "id": "uuid-...",
    "title": "노트 제목"
  }
}
```

---

### 6. 비밀번호 변경 기능 개선 ✅

#### `change_password` 함수 개선
- 편집 비밀번호와 열람 비밀번호 구분
- `password_type` 파라미터로 구분 (기본값: 'edit')

---

## 데이터베이스 마이그레이션

### 생성된 마이그레이션 파일
- `notes/migrations/0003_sharelink_permissions.py`
  - `permission` 필드 추가
  - `view_password_hash` 필드 추가

### 마이그레이션 실행 방법
```bash
python manage.py migrate notes
```

---

## 의존성 추가

### requirements.txt 업데이트
```
qrcode[pil]>=7.4.2
```

### 설치 방법
```bash
pip install qrcode[pil]
```

---

## API 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/s/create/` | 공유 링크 생성 (권한 설정 가능) |
| GET | `/s/{token}/` | 공유 링크 조회 (권한 검증) |
| POST | `/s/{token}/edit/` | 편집 권한 인증 |
| POST | `/s/{token}/change-password/` | 비밀번호 변경 |
| GET | `/api/shares/{token}/qr/` | QR 코드 생성 |
| GET | `/api/shares/{token}/info/` | 링크 정보 조회 |

---

## 권한 및 보안

### 읽기 전용 링크 (read)
- 노트 내용 조회만 가능
- 편집 버튼 숨김
- 편집 비밀번호 설정 불필요

### 편집 가능 링크 (edit)
- 노트 내용 조회 및 편집 가능
- 편집 비밀번호 선택적 설정
- 비밀번호 없으면 자동 편집 세션 부여

### 비밀번호 보안
- 열람 비밀번호: 노트 조회 전 검증
- 편집 비밀번호: 노트 편집 전 검증
- Django의 PBKDF2 해싱 사용

---

## 사용 예시

### 읽기 전용 링크 생성
```javascript
const formData = new FormData();
formData.append('note_id', noteId);
formData.append('permission', 'read');
formData.append('view_password', 'view123');

const response = await fetch('/s/create/', {
  method: 'POST',
  body: formData,
  headers: {
    'X-CSRFToken': getCsrfToken()
  }
});

const data = await response.json();
console.log('공유 링크:', data.url);
```

### 편집 가능 링크 생성
```javascript
const formData = new FormData();
formData.append('note_id', noteId);
formData.append('permission', 'edit');
formData.append('edit_password', 'edit123');

const response = await fetch('/s/create/', {
  method: 'POST',
  body: formData,
  headers: {
    'X-CSRFToken': getCsrfToken()
  }
});

const data = await response.json();
console.log('공유 링크:', data.url);
```

### QR 코드 생성 및 표시
```javascript
// QR 코드 생성
const response = await fetch(`/api/shares/${token}/qr/`);
const data = await response.json();

// SVG로 표시
const qrContainer = document.getElementById('qr-code');
qrContainer.innerHTML = data.qr_code_svg;

// 또는 이미지로 표시
const img = document.createElement('img');
img.src = `data:image/svg+xml;base64,${data.qr_code_base64}`;
document.body.appendChild(img);
```

---

## 다음 단계 (Phase 5)

1. **플랜 관리**
   - 결제 연동
   - 플랜별 기능 제한 미들웨어

2. **AI 프롬프트 기능**
   - AI 서비스 연동 (OpenAI, Claude 등)
   - Pro 플랜 전용 기능
   - 프롬프트 사용량 추적

---

## 완료된 TODO

- ✅ QR 코드 생성 라이브러리 추가 및 설정
- ✅ 공유 링크 QR 코드 생성 API
- ✅ ShareLink 모델에 권한 필드 추가 (read_only, edit)
- ✅ 공유 링크 생성 시 권한 설정 기능
- ✅ 공유 링크 조회 시 권한 검증 로직
- ✅ 공유 링크 편집 시 권한 검증 로직

---

## 주의사항

1. **QR 코드 라이브러리**: `qrcode[pil]` 패키지가 설치되어 있어야 합니다.
2. **하위 호환성**: 파일 기반 저장소의 기존 공유 링크도 계속 지원됩니다.
3. **비밀번호**: 열람 비밀번호와 편집 비밀번호를 별도로 설정할 수 있습니다.


