(function () {
  const stepView = document.getElementById('stepView');
  const live = document.getElementById('live');
  const btnInc = document.getElementById('btnInc');
  const btnDec = document.getElementById('btnDec');
  const btnContrast = document.getElementById('btnContrast');
  const btnSpeak = document.getElementById('btnSpeak');
  const form = document.getElementById('routeForm');
  const latEl = document.getElementById('lat');
  const lngEl = document.getElementById('lng');

  let steps = [], idx = 0, baseFont = 1.125;
  function speak(t){ try{ speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(t); u.lang='ko-KR'; u.rate=0.9; speechSynthesis.speak(u);}catch(e){} }
  function vibrate(ms){ if(navigator.vibrate) navigator.vibrate(ms); }
  const icon = t => t==='turn_right'?'➡️':t==='turn_left'?'⬅️':t==='crosswalk'?'🚸':t==='arrive'?'🏁':'⬆️';

  function render(){
    if(!steps.length){ stepView.innerHTML='<p>경로를 불러오세요.</p>'; return; }
    const s = steps[idx];
    stepView.innerHTML = `
      <div class="big-arrow" aria-hidden="true">${icon(s.type)}</div>
      <div class="step">${s.text}</div>
      <div class="meta">거리 약 ${s.distance_m}m · 지형: ${s.slope}${s.crosswalk?' · 횡단보도':''}${s.landmark?' · 랜드마크: '+s.landmark:''}</div>
      <div class="meta">${idx+1}/${steps.length}</div>`;
    stepView.focus(); live.textContent = s.text; vibrate(40);
  }

  document.getElementById('btnLocate').addEventListener('click', ()=>{
    if(!navigator.geolocation){ alert('이 브라우저는 위치 기능을 지원하지 않습니다.'); return; }
    navigator.geolocation.getCurrentPosition(p=>{
      latEl.value = p.coords.latitude.toFixed(6);
      lngEl.value = p.coords.longitude.toFixed(6);
    }, ()=> alert('위치 권한이 거부되었습니다.'));
  });

  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const stopId = document.getElementById('stop').value;
    const pref = document.getElementById('pref').value;
    const lat = parseFloat(latEl.value), lng = parseFloat(lngEl.value);
    const params = new URLSearchParams({
      origin_lat: Number.isFinite(lat)? lat : 37.5663,
      origin_lng: Number.isFinite(lng)? lng : 126.9779,
      stop_id: String(stopId), pref
    });
    const res = await fetch(`/api/route/?${params.toString()}`);
    const data = await res.json();
    steps = data.steps || []; idx = 0; render(); if(steps[0]) speak(steps[0].text);
  });

  btnInc.addEventListener('click', ()=>{ baseFont+=.125; document.body.style.fontSize=baseFont+'rem'; });
  btnDec.addEventListener('click', ()=>{ baseFont=Math.max(1, baseFont-.125); document.body.style.fontSize=baseFont+'rem'; });
  btnContrast.addEventListener('click', ()=>{ const on=document.body.classList.toggle('high-contrast'); btnContrast.setAttribute('aria-pressed', on?'true':'false'); });
  btnSpeak.addEventListener('click', ()=>{ if(steps[idx]) speak(steps[idx].text); });

  window.addEventListener('keydown', e=>{
    if(!steps.length) return;
    if(e.key==='ArrowRight'){ idx=Math.min(idx+1, steps.length-1); render(); speak(steps[idx].text); }
    if(e.key==='ArrowLeft'){ idx=Math.max(idx-1, 0); render(); speak(steps[idx].text); }
    if(e.key.toLowerCase()==='s') speak(steps[idx].text);
    if(e.key.toLowerCase()==='h') btnContrast.click();
    if(e.key==='=') btnInc.click();
    if(e.key==='-') btnDec.click();
  });
})();
