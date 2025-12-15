# Phase 3 구현 완료 요약 - 미디어 파일 확장

## 구현 완료된 기능

### 1. 파일 검증 유틸리티 ✅

#### `notes/utils.py` 생성
- **이미지 검증**: `validate_image(file)`
  - 허용 타입: PNG, JPEG, WebP, GIF
  - 최대 크기: 10MB
  
- **음성 검증**: `validate_audio(file)`
  - 허용 타입: MP3, WAV, OGG, WebM, M4A
  - 최대 크기: 50MB
  
- **영상 검증**: `validate_video(file)`
  - 허용 타입: MP4, WebM, OGG, MOV
  - 최대 크기: 100MB

#### 검증 기능
- MIME 타입 검증
- 파일 확장자 검증
- 파일 크기 제한 검증
- 타입별 허용 목록 관리

---

### 2. 음성 파일 업로드 API ✅

#### 엔드포인트
- `POST /api/media/upload-audio/`

#### 기능
- 음성 파일 업로드 및 검증
- MediaFile 모델에 저장
- 회원/비회원 모두 지원
- 파일 ID 및 URL 반환

#### 요청 예시
```bash
curl -X POST http://localhost:8000/api/media/upload-audio/ \
  -H "Cookie: sessionid=<session_id>" \
  -F "file=@audio.mp3"
```

#### 응답 예시
```json
{
  "success": true,
  "url": "/media/media/audio/1/uuid.mp3",
  "file_id": "uuid-...",
  "file_type": "audio",
  "file_size": 5242880
}
```

---

### 3. 영상 파일 업로드 API ✅

#### 엔드포인트
- `POST /api/media/upload-video/`

#### 기능
- 영상 파일 업로드 및 검증
- MediaFile 모델에 저장
- 회원/비회원 모두 지원
- 파일 ID 및 URL 반환

#### 요청 예시
```bash
curl -X POST http://localhost:8000/api/media/upload-video/ \
  -H "Cookie: sessionid=<session_id>" \
  -F "file=@video.mp4"
```

#### 응답 예시
```json
{
  "success": true,
  "url": "/media/media/video/1/uuid.mp4",
  "file_id": "uuid-...",
  "file_type": "video",
  "file_size": 10485760
}
```

---

### 4. 파일 목록 조회 API ✅

#### 엔드포인트
- `GET /api/media/files/`
- Query params: `?file_type=image|audio|video` (선택)

#### 기능
- 사용자가 업로드한 파일 목록 조회
- 파일 타입별 필터링 지원
- 최근 100개만 반환

#### 요청 예시
```bash
curl -X GET "http://localhost:8000/api/media/files/?file_type=audio" \
  -H "Cookie: sessionid=<session_id>"
```

#### 응답 예시
```json
{
  "success": true,
  "files": [
    {
      "id": "uuid-...",
      "file_type": "audio",
      "mime_type": "audio/mpeg",
      "file_size": 5242880,
      "url": "/media/media/audio/1/uuid.mp3",
      "created_at": "2025-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

---

### 5. 파일 정보 조회 API ✅

#### 엔드포인트
- `GET /api/media/files/{file_id}/`

#### 기능
- 특정 파일의 상세 정보 조회
- 업로더만 조회 가능 (권한 검증)

#### 요청 예시
```bash
curl -X GET http://localhost:8000/api/media/files/{file_id}/ \
  -H "Cookie: sessionid=<session_id>"
```

#### 응답 예시
```json
{
  "success": true,
  "file": {
    "id": "uuid-...",
    "file_type": "audio",
    "mime_type": "audio/mpeg",
    "file_size": 5242880,
    "url": "/media/media/audio/1/uuid.mp3",
    "created_at": "2025-01-01T12:00:00Z"
  }
}
```

---

### 6. 기존 이미지 업로드 개선 ✅

#### `upload_image` 함수 개선
- 파일 검증 유틸리티 사용
- 회원인 경우 MediaFile 모델에 저장
- 기존 기능 유지 (하위 호환성)

---

## 파일 저장 구조

### 회원 파일
```
media/
  audio/
    {user_id}/
      {uuid}.mp3
  video/
    {user_id}/
      {uuid}.mp4
```

### 비회원 파일
```
media/
  audio/
    {client_token}/
      {uuid}.mp3
  video/
    {client_token}/
      {uuid}.mp4
```

---

## 허용된 파일 타입 및 크기

### 이미지
- **타입**: PNG, JPEG, WebP, GIF
- **크기**: 최대 10MB
- **처리**: 자동 리사이징 (2000px 초과 시)

### 음성
- **타입**: MP3, WAV, OGG, WebM, M4A
- **크기**: 최대 50MB
- **처리**: 원본 저장

### 영상
- **타입**: MP4, WebM, OGG, MOV
- **크기**: 최대 100MB
- **처리**: 원본 저장

---

## 보안 기능

### 파일 검증
- MIME 타입 검증
- 파일 확장자 검증
- 파일 크기 제한
- 허용 목록 기반 검증

### 권한 관리
- 업로더만 파일 조회 가능
- 회원/비회원 구분
- 파일 소유권 확인

---

## API 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/upload-image/` | 이미지 업로드 (기존) |
| POST | `/api/media/upload-audio/` | 음성 파일 업로드 |
| POST | `/api/media/upload-video/` | 영상 파일 업로드 |
| GET | `/api/media/files/` | 파일 목록 조회 |
| GET | `/api/media/files/{file_id}/` | 파일 정보 조회 |

---

## 다음 단계 (Phase 4)

1. **공유 기능 고도화**
   - QR 코드 생성
   - 공유 권한 세분화 (읽기/편집)

2. **플랜 관리**
   - 결제 연동
   - 플랜별 기능 제한 미들웨어

3. **AI 프롬프트 기능**
   - AI 서비스 연동
   - Pro 플랜 전용 기능

---

## 완료된 TODO

- ✅ 음성 파일 업로드 API 구현
- ✅ 영상 파일 업로드 API 구현
- ✅ 파일 타입별 검증 강화 (MIME 타입, 확장자)
- ✅ MediaFile 모델을 활용한 파일 저장
- ✅ 파일 크기 제한 설정 (음성/영상별)
- ✅ 파일 목록 조회 API

---

## 사용 예시

### 음성 파일 업로드
```javascript
const formData = new FormData();
formData.append('file', audioFile);

const response = await fetch('/api/media/upload-audio/', {
  method: 'POST',
  body: formData,
  headers: {
    'X-CSRFToken': getCsrfToken()
  }
});

const data = await response.json();
console.log('업로드된 파일 URL:', data.url);
```

### 영상 파일 업로드
```javascript
const formData = new FormData();
formData.append('file', videoFile);

const response = await fetch('/api/media/upload-video/', {
  method: 'POST',
  body: formData,
  headers: {
    'X-CSRFToken': getCsrfToken()
  }
});

const data = await response.json();
console.log('업로드된 파일 URL:', data.url);
```

### 파일 목록 조회
```javascript
const response = await fetch('/api/media/files/?file_type=audio');
const data = await response.json();
console.log('업로드한 음성 파일:', data.files);
```


