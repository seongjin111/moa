# Phase 5 구현 완료 요약 - 플랜 관리 및 AI 프롬프트 기능

## 구현 완료된 기능

### 1. 플랜별 기능 제한 시스템 ✅

#### 데코레이터 구현
- **`require_pro_plan`**: Pro 플랜이 필요한 기능에 사용
- **`check_ai_usage_limit`**: AI 사용량 제한 확인 (일일 100회)

#### 기능 제한
- 무료 플랜: 기본 기능만 사용 가능
- Pro 플랜: AI 프롬프트 기능 사용 가능

---

### 2. AI 프롬프트 모델 설계 ✅

#### AIPromptUsage 모델
- 프롬프트 및 응답 저장
- AI 서비스 제공자 (OpenAI, Claude, Gemini)
- 사용한 모델 정보
- 토큰 사용량 추적
- 비용 추정 (USD)
- 사용 시간 기록

---

### 3. AI 서비스 연동 ✅

#### 지원 AI 서비스
- **OpenAI**: GPT-3.5-turbo, GPT-4 등
- **Claude (Anthropic)**: Claude 3 Sonnet, Opus 등
- **Gemini**: 향후 지원 예정

#### `core/services/ai_service.py`
- 통합 AI 호출 인터페이스
- 제공자별 API 호출 메서드
- 비용 추정 기능

---

### 4. AI 프롬프트 API ✅

#### 프롬프트 전송
- `POST /api/ai/prompt/`
- Pro 플랜 전용
- 일일 사용량 제한 확인 (100회)

#### 요청 예시
```bash
curl -X POST http://localhost:8000/api/ai/prompt/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=<session_id>" \
  -d '{
    "prompt": "다음 텍스트를 요약해주세요: ...",
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "max_tokens": 1000
  }'
```

#### 응답 예시
```json
{
  "success": true,
  "response": "요약된 내용...",
  "usage": {
    "id": "uuid-...",
    "tokens_used": 150,
    "cost": 0.0003,
    "provider": "openai",
    "model": "gpt-3.5-turbo"
  },
  "quota": {
    "used_today": 5,
    "limit_today": 100,
    "remaining_today": 95
  }
}
```

---

### 5. AI 사용량 통계 API ✅

#### 사용량 통계 조회
- `GET /api/ai/usage/`
- Query params: `?days=7` (선택, 기본값: 7일)

#### 오늘 사용량 조회
- `GET /api/ai/usage/today/`

#### 응답 예시
```json
{
  "success": true,
  "period_days": 7,
  "summary": {
    "total_requests": 25,
    "total_tokens": 3750,
    "total_cost": 0.0075,
    "average_tokens_per_request": 150
  },
  "by_provider": {
    "openai": {
      "count": 20,
      "tokens": 3000,
      "cost": 0.006
    },
    "claude": {
      "count": 5,
      "tokens": 750,
      "cost": 0.0015
    }
  },
  "recent_usages": [...]
}
```

---

## 환경 설정

### API 키 설정

#### 방법 1: 환경 변수 사용 (권장)
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### 방법 2: settings.py 직접 설정 (개발용)
```python
OPENAI_API_KEY = 'sk-...'
ANTHROPIC_API_KEY = 'sk-ant-...'
```

---

## 의존성 추가

### requirements.txt 업데이트
```
openai>=1.0.0
anthropic>=0.18.0
```

### 설치 방법
```bash
pip install openai anthropic
```

---

## 사용량 제한

### Pro 플랜 제한
- 일일 AI 프롬프트: 100회
- 자정에 자동 리셋
- 사용량 초과 시 429 에러 반환

### 비용 추정
- OpenAI GPT-3.5-turbo: $0.002 per 1K tokens
- OpenAI GPT-4: $0.03 per 1K tokens
- Claude Sonnet: $0.003 per 1K tokens
- Claude Opus: $0.015 per 1K tokens

---

## API 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 | 플랜 |
|--------|-----------|------|------|
| POST | `/api/ai/prompt/` | AI 프롬프트 전송 | Pro |
| GET | `/api/ai/usage/` | 사용량 통계 조회 | Pro |
| GET | `/api/ai/usage/today/` | 오늘 사용량 조회 | Pro |

---

## 사용 예시

### AI 프롬프트 전송
```javascript
const response = await fetch('/api/ai/prompt/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  },
  body: JSON.stringify({
    prompt: '다음 텍스트를 요약해주세요: ...',
    provider: 'openai',
    model: 'gpt-3.5-turbo',
    max_tokens: 1000
  })
});

const data = await response.json();
if (data.success) {
  console.log('AI 응답:', data.response);
  console.log('사용량:', data.usage);
  console.log('남은 사용량:', data.quota.remaining_today);
}
```

### 사용량 통계 조회
```javascript
const response = await fetch('/api/ai/usage/?days=30');
const data = await response.json();

console.log('총 요청 수:', data.summary.total_requests);
console.log('총 토큰:', data.summary.total_tokens);
console.log('총 비용:', data.summary.total_cost);
console.log('제공자별 통계:', data.by_provider);
```

---

## 데이터베이스 마이그레이션

### 생성된 마이그레이션 파일
- `core/migrations/0003_ai_prompt_usage.py` - AIPromptUsage 모델

### 마이그레이션 실행 방법
```bash
python manage.py migrate core
```

---

## 관리자 페이지

### AIPromptUsage Admin
- 목록: 사용자, 제공자, 모델, 토큰 수, 비용, 생성일
- 필터: 제공자, 생성일
- 검색: 사용자명, 이메일, 프롬프트

---

## 보안 및 제한

### 플랜 검증
- Pro 플랜만 AI 기능 사용 가능
- 데코레이터로 자동 검증

### 사용량 제한
- 일일 100회 제한
- 사용량 초과 시 429 에러

### API 키 보안
- 환경 변수로 관리 권장
- settings.py에 직접 저장하지 않기

---

## 다음 단계

1. **결제 연동** (선택사항)
   - 결제 서비스 연동 (예: 아임포트, 토스페이먼츠)
   - 플랜 업그레이드 기능

2. **추가 기능**
   - AI 응답 히스토리 관리
   - 프롬프트 템플릿 기능
   - 배치 처리 기능

---

## 완료된 TODO

- ✅ 플랜별 기능 제한 미들웨어 구현
- ✅ AI 프롬프트 모델 설계 (사용량 추적)
- ✅ AI 프롬프트 API 구현 (OpenAI/Claude 연동)
- ✅ Pro 플랜 전용 기능 제한 로직
- ✅ AI 사용량 추적 및 제한

---

## 주의사항

1. **API 키 보안**: 환경 변수로 관리하거나 Django의 secrets 관리 기능 사용
2. **비용 관리**: 사용량 모니터링 및 알림 설정 권장
3. **에러 처리**: AI 서비스 장애 시 적절한 에러 메시지 반환
4. **라이브러리 설치**: `pip install openai anthropic` 필요


