(function () {
  // DOM 참조
  const stepView = document.getElementById('stepView');
  const live = document.getElementById('live');
  const btnInc = document.getElementById('btnInc');
  const btnDec = document.getElementById('btnDec');
  const btnContrast = document.getElementById('btnContrast');
  const btnSpeak = document.getElementById('btnSpeak');
  const form = document.getElementById('routeForm');
  const latEl = document.getElementById('lat');
  const lngEl = document.getElementById('lng');

  // 상태
  let steps = [];
  let idx = 0;
  let baseFont = 1.125; // rem

  // 정류장 (샘플)
  const BUS_STOPS = {
    1: { id: 1, name: '중앙시장 정류장', lat: 37.5661, lng: 126.9778, has_shelter: true },
    2: { id: 2, name: '시청 앞 정류장', lat: 37.56645, lng: 126.97835, has_shelter: true },
  };

  // 접근성: 음성
  function speak(text) {
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'ko-KR';
      u.rate = 0.9;
      speechSynthesis.speak(u);
    } catch (e) {
      // 미지원 장치
    }
  }

  // 접근성: 진동(모바일)
  function vibrate(ms) {
    if (navigator.vibrate) navigator.vibrate(ms);
  }

  // 아이콘 매핑
  function iconFor(type) {
    switch (type) {
      case 'turn_right': return '➡️';
      case 'turn_left': return '⬅️';
      case 'crosswalk': return '🚸';
      case 'arrive': return '🏁';
      default: return '⬆️';
    }
  }

  // 렌더링
  function render() {
    if (!steps.length) {
      stepView.innerHTML = '<p>경로를 불러오세요.</p>';
      return;
    }
    const s = steps[idx];
    const arrow = iconFor(s.type);
    stepView.innerHTML = `
      <div class="big-arrow" aria-hidden="true">${arrow}</div>
      <div class="step">${s.text}</div>
      <div class="meta">
        거리 약 ${s.distance_m}m · 지형: ${s.slope}
        ${s.crosswalk ? ' · 횡단보도' : ''}${s.landmark ? ' · 랜드마크: ' + s.landmark : ''}
      </div>
      <div class="meta">${idx + 1}/${steps.length}</div>
    `;
    stepView.focus();
    live.textContent = s.text; // 스크린리더 알림
    vibrate(40);
  }

  // 프론트 전용 모킹 라우팅(안전 우회/횡단보도 우선 흉내)
  function mockRoute({ origin, stop, pref }) {
    const common = [
      {
        type: 'depart',
        text: '현재 위치에서 북쪽으로 50미터 직진',
        distance_m: 50, landmark: '편의점 앞', crosswalk: false, slope: '완만', bearing: 'N',
      },
      {
        type: 'turn_right',
        text: '오른쪽으로 꺾어 80미터 진행 (인도 넓음)',
        distance_m: 80, landmark: '은행 건물', crosswalk: false, slope: '평지', bearing: 'E',
      },
      {
        type: 'crosswalk',
        text: '신호등 있는 횡단보도를 건너세요',
        distance_m: 15, landmark: '큰 사거리', crosswalk: true, slope: '평지', bearing: 'E',
      },
      {
        type: 'arrive',
        text: `${stop.name} 도착 (쉼터 ${stop.has_shelter ? '있음' : '없음'})`,
        distance_m: 0, landmark: '버스 정류장', crosswalk: false, slope: '평지', bearing: 'E',
      },
    ];

    // 선호도에 따라 보조 정보 추가
    if (pref === 'low-vision') {
      common.forEach(s => (s.tts_hint = s.text));
    } else if (pref === 'low-hearing') {
      common.forEach(s => (s.caption = s.text));
    }
    return common;
  }

  // 현재 위치 버튼
  document.getElementById('btnLocate').addEventListener('click', () => {
    if (!navigator.geolocation) {
      alert('이 브라우저는 위치 기능을 지원하지 않습니다.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        latEl.value = pos.coords.latitude.toFixed(6);
        lngEl.value = pos.coords.longitude.toFixed(6);
      },
      () => alert('위치 권한이 거부되었습니다.')
    );
  });

  // 폼 제출 → 모킹 경로 생성
  form.addEventListener('submit', e => {
    e.preventDefault();
    const stopId = document.getElementById('stop').value;
    const pref = document.getElementById('pref').value;
    const origin_lat = parseFloat(latEl.value);
    const origin_lng = parseFloat(lngEl.value);
    const origin = {
      lat: Number.isFinite(origin_lat) ? origin_lat : 37.5663,
      lng: Number.isFinite(origin_lng) ? origin_lng : 126.9779,
    };
    const stop = BUS_STOPS[stopId] || BUS_STOPS[1];
    steps = mockRoute({ origin, stop, pref });
    idx = 0;
    render();
    if (steps[0]) speak(steps[0].text);
  });

  // 보기 설정
  btnInc.addEventListener('click', () => {
    baseFont += 0.125;
    document.body.style.fontSize = baseFont + 'rem';
  });
  btnDec.addEventListener('click', () => {
    baseFont = Math.max(1, baseFont - 0.125);
    document.body.style.fontSize = baseFont + 'rem';
  });
  btnContrast.addEventListener('click', () => {
    const active = document.body.classList.toggle('high-contrast');
    btnContrast.setAttribute('aria-pressed', active ? 'true' : 'false');
  });
  btnSpeak.addEventListener('click', () => {
    if (steps[idx]) speak(steps[idx].text);
  });

  // 키보드 단축키
  window.addEventListener('keydown', e => {
    if (!steps.length) return;
    const k = e.key;
    if (k === 'ArrowRight') {
      idx = Math.min(steps.length - 1, idx + 1);
      render();
      speak(steps[idx].text);
    }
    if (k === 'ArrowLeft') {
      idx = Math.max(0, idx - 1);
      render();
      speak(steps[idx].text);
    }
    if (k.toLowerCase() === 's') speak(steps[idx].text);
    if (k.toLowerCase() === 'h') btnContrast.click();
    if (k === '=') btnInc.click();
    if (k === '-') btnDec.click();
  });
})();
