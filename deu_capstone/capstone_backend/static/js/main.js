/* ========= utilities ========= */

function $(sel) {
  return document.querySelector(sel);
}
function $all(sel) {
  return document.querySelectorAll(sel);
}
function createEl(tag, cls) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

function toast(msg) {
  const c = $("#toastContainer");
  const t = createEl("div", "toast");
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

/* ========= 저장 구조 ========= */

const STORAGE_KEY = "minji-notebook-v3";

let state = {
  sections: [],
  currentSectionId: null,
  currentPageId: null,
};

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function load() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      state = JSON.parse(raw);
    } catch {}
  }

  if (!state.sections.length) {
    const sec = createSection("섹션 1");
    createPage(sec.id, "페이지 1", "새 페이지");
  }
  if (!state.currentSectionId) {
    state.currentSectionId = state.sections[0].id;
  }
  const sec = getCurrentSection();
  if (sec && !sec.pages.length)
    createPage(sec.id, "페이지 1", "새 페이지");
  if (!state.currentPageId)
    state.currentPageId = getCurrentSection().pages[0].id;
}

function getCurrentSection() {
  return state.sections.find((s) => s.id === state.currentSectionId);
}
function getCurrentPage() {
  const sec = getCurrentSection();
  if (!sec) return null;
  return sec.pages.find((p) => p.id === state.currentPageId);
}

/* ========= Section / Page 생성 ========= */

function createSection(title = "섹션") {
  const id = "sec_" + Math.random().toString(36).slice(2);
  const sec = { id, title, pages: [] };
  state.sections.push(sec);
  state.currentSectionId = id;
  save();
  return sec;
}

function createPage(sectionId, title = "페이지", subtitle = "새 페이지") {
  const sec = state.sections.find((s) => s.id === sectionId);
  const id = "page_" + Math.random().toString(36).slice(2);

  const page = {
    id,
    title,
    subtitle,
    background: "white",
    pattern: "none",
    zoom: 1,
    textHtml: "",
    ink: "",
    objects: [],
  };

  sec.pages.push(page);
  state.currentPageId = id;
  save();
  return page;
}

/* ========= UI 렌더링 ========= */

function renderSections() {
  const ul = $("#sectionList");
  ul.innerHTML = "";

  state.sections.forEach((sec) => {
    const li = createEl("li", "list-item" + (sec.id === state.currentSectionId ? " active" : ""));
    const title = createEl("span", "list-title");
    title.textContent = sec.title;

    const actions = createEl("div", "list-actions");

    const rename = createEl("button", "list-action-btn");
    rename.textContent = "✏";
    rename.onclick = (e) => {
      e.stopPropagation();
      const name = prompt("섹션 이름", sec.title);
      if (name) {
        sec.title = name;
        save();
        renderSections();
      }
    };

    const del = createEl("button", "list-action-btn");
    del.textContent = "✕";
    del.onclick = (e) => {
      e.stopPropagation();
      if (!confirm("정말 삭제할까요?")) return;
      state.sections = state.sections.filter((s) => s.id !== sec.id);

      if (!state.sections.length) {
        const s = createSection("섹션 1");
        createPage(s.id, "페이지 1", "새 페이지");
      }

      if (!state.currentSectionId)
        state.currentSectionId = state.sections[0].id;
      save();
      renderSections();
      renderPages();
      loadPageToUI();
    };

    actions.append(rename, del);
    li.append(title, actions);

    title.onclick = () => {
      state.currentSectionId = sec.id;
      if (!sec.pages.length)
        createPage(sec.id, "페이지", "새 페이지");
      state.currentPageId = sec.pages[0].id;
      save();
      renderSections();
      renderPages();
      loadPageToUI();
    };

    ul.appendChild(li);
  });
}

function renderPages() {
  const sec = getCurrentSection();
  const ul = $("#pageList");
  ul.innerHTML = "";
  if (!sec) return;

  sec.pages.forEach((page) => {
    const li = createEl("li", "list-item" + (page.id === state.currentPageId ? " active" : ""));
    const title = createEl("span", "list-title");
    title.textContent = page.subtitle || page.title;

    const actions = createEl("div", "list-actions");
    const rename = createEl("button", "list-action-btn");
    rename.textContent = "✏";
    rename.onclick = (e) => {
      e.stopPropagation();
      const name = prompt("부제목", page.subtitle);
      if (name) {
        page.subtitle = name;
        save();
        renderPages();
      }
    };

    const del = createEl("button", "list-action-btn");
    del.textContent = "✕";
    del.onclick = (e) => {
      e.stopPropagation();
      if (!confirm("페이지 삭제?")) return;
      sec.pages = sec.pages.filter((p) => p.id !== page.id);

      if (!sec.pages.length)
        createPage(sec.id, "페이지", "새 페이지");
      state.currentPageId = sec.pages[0].id;

      save();
      renderPages();
      loadPageToUI();
    };

    actions.append(rename, del);
    li.append(title, actions);

    title.onclick = () => {
      state.currentPageId = page.id;
      save();
      renderPages();
      loadPageToUI();
    };

    ul.appendChild(li);
  });
}

/* ========= 페이지 UI 반영 ========= */

const textEditor = $("#textEditor");
const noteArea = $("#noteArea");
const inkCanvas = $("#inkCanvas");
const inkCtx = inkCanvas.getContext("2d");
const objectLayer = $("#objectLayer");

function loadPageToUI() {
  const p = getCurrentPage();
  if (!p) return;

  // 제목
  $("#pageTitleInput").value = p.title;
  $("#pageSubtitleInput").value = p.subtitle;

  // 배경
  noteArea.classList.remove("bg-white", "bg-ivory", "bg-black");
  noteArea.classList.add("bg-" + p.background);

  // 패턴
  noteArea.classList.remove("pattern-grid", "pattern-lines", "pattern-dots");
  if (p.pattern === "grid") noteArea.classList.add("pattern-grid");
  if (p.pattern === "lines") noteArea.classList.add("pattern-lines");
  if (p.pattern === "dots") noteArea.classList.add("pattern-dots");

  // 줌
  const zoom = p.zoom || 1;
  $("#zoomSlider").value = zoom * 100;
  $("#zoomLabel").textContent = Math.round(zoom * 100) + "%";
  noteArea.style.transform = `scale(${zoom})`;

  // 텍스트
  textEditor.innerHTML = p.textHtml || "";

  // 필기
  resizeInkCanvas();
  if (p.ink) {
    const img = new Image();
    img.onload = () => inkCtx.drawImage(img, 0, 0, inkCanvas.width, inkCanvas.height);
    img.src = p.ink;
  } else {
    inkCtx.clearRect(0, 0, inkCanvas.width, inkCanvas.height);
  }

  // 오브젝트
  objectLayer.innerHTML = "";
  p.objects.forEach((obj) => {
    if (obj.type === "image") spawnImage(obj);
    if (obj.type === "textbox") spawnTextbox(obj);
  });
}

$("#pageTitleInput").oninput = () => {
  const p = getCurrentPage();
  p.title = $("#pageTitleInput").value;
  save();
  renderPages();
};

$("#pageSubtitleInput").oninput = () => {
  const p = getCurrentPage();
  p.subtitle = $("#pageSubtitleInput").value;
  save();
  renderPages();
};

textEditor.oninput = () => {
  const p = getCurrentPage();
  p.textHtml = textEditor.innerHTML;
  save();
};

/* ========= 드로잉 시스템 ========= */

let drawMode = "pen";
let drawing = false;
let inkColor = "#e91e63";
let inkThickness = 4;
let lastX = 0;
let lastY = 0;
let undoStack = [];
let redoStack = [];

function resizeInkCanvas() {
  const rect = noteArea.getBoundingClientRect();
  inkCanvas.width = rect.width;
  inkCanvas.height = rect.height;
}

window.addEventListener("resize", () => {
  resizeInkCanvas();
  loadPageToUI();
});

// draw 탭일 때만 pointer-events 활성화
function updateInkEvents() {
  const active = document.querySelector(".menu-tab.active").dataset.tab;
  inkCanvas.style.pointerEvents = active === "draw" ? "auto" : "none";
}
$all(".menu-tab").forEach((b) => b.addEventListener("click", updateInkEvents));

// 마우스 이벤트
inkCanvas.addEventListener("mousedown", (e) => {
  if (inkCanvas.style.pointerEvents === "none") return;
  undoStack.push(inkCanvas.toDataURL());
  redoStack = [];
  drawing = true;
  const pos = getPos(e);
  lastX = pos.x;
  lastY = pos.y;
  startStroke();
});

inkCanvas.addEventListener("mousemove", (e) => {
  if (!drawing) return;
  drawStroke(e);
});

window.addEventListener("mouseup", () => {
  if (drawing) endStroke();
});

function startStroke() {
  inkCtx.lineCap = "round";
  inkCtx.lineJoin = "round";
  inkCtx.globalCompositeOperation = "source-over";
  inkCtx.strokeStyle = inkColor;
  inkCtx.lineWidth = inkThickness;
  if (drawMode === "highlighter") {
    inkCtx.strokeStyle = hexToRGBA(inkColor, 0.3);
    inkCtx.lineWidth = inkThickness * 2;
  }
  if (drawMode === "eraser") {
    inkCtx.globalCompositeOperation = "destination-out";
    inkCtx.lineWidth = inkThickness;
  }
  inkCtx.beginPath();
  inkCtx.moveTo(lastX, lastY);
}

function drawStroke(e) {
  const pos = getPos(e);
  inkCtx.lineTo(pos.x, pos.y);
  inkCtx.stroke();
  lastX = pos.x;
  lastY = pos.y;
}

function endStroke() {
  drawing = false;
  saveInk();
}

function saveInk() {
  const p = getCurrentPage();
  p.ink = inkCanvas.toDataURL();
  save();
}

function getPos(e) {
  const r = inkCanvas.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
}

function hexToRGBA(hex, a) {
  const c = hex.replace("#", "");
  const n = parseInt(c, 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r},${g},${b},${a})`;
}

// 모드 버튼
$all(".mode-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    $all(".mode-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    drawMode = btn.dataset.mode;
  })
);

// 색/두께
$("#inkColorPicker").onchange = () => {
  inkColor = $("#inkColorPicker").value;
};
$("#inkThickness").oninput = () => {
  inkThickness = parseInt($("#inkThickness").value);
  $("#inkThicknessLabel").textContent = inkThickness + " px";
};

// 되돌리기
$("#undoInkBtn").onclick = () => {
  if (!undoStack.length) return;
  redoStack.push(inkCanvas.toDataURL());
  const img = new Image();
  img.onload = () => {
    inkCtx.clearRect(0, 0, inkCanvas.width, inkCanvas.height);
    inkCtx.drawImage(img, 0, 0, inkCanvas.width, inkCanvas.height);
    saveInk();
  };
  img.src = undoStack.pop();
};

// 다시하기
$("#redoInkBtn").onclick = () => {
  if (!redoStack.length) return;
  undoStack.push(inkCanvas.toDataURL());
  const img = new Image();
  img.onload = () => {
    inkCtx.clearRect(0, 0, inkCanvas.width, inkCanvas.height);
    inkCtx.drawImage(img, 0, 0, inkCanvas.width, inkCanvas.height);
    saveInk();
  };
  img.src = redoStack.pop();
};

// 전체 지우기
$("#clearInkBtn").onclick = () => {
  inkCtx.clearRect(0, 0, inkCanvas.width, inkCanvas.height);
  saveInk();
};

/* ========= 이미지 삽입 ========= */

$("#insertImageBtn").onclick = () => $("#imageInput").click();

$("#imageInput").onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const url = URL.createObjectURL(file);

  const obj = {
    id: "obj_" + Math.random().toString(36).slice(2),
    type: "image",
    src: url,
    left: 200,
    top: 200,
    width: 300,
    height: "auto",
  };

  getCurrentPage().objects.push(obj);
  save();
  spawnImage(obj);

  e.target.value = "";
};

function spawnImage(obj) {
  const wrap = createEl("div", "image-wrapper");
  wrap.dataset.id = obj.id;
  wrap.style.left = obj.left + "px";
  wrap.style.top = obj.top + "px";

  const img = createEl("img");
  img.src = obj.src;
  img.style.width = obj.width + "px";

  const handle = createEl("div", "resize-handle");

  wrap.append(img, handle);
  objectLayer.appendChild(wrap);

  enableDrag(wrap);
  enableResize(wrap, img, handle);
}

/* ========= 텍스트 박스 ========= */

$("#addTextBoxBtn").onclick = () => {
  const obj = {
    id: "obj_" + Math.random().toString(36).slice(2),
    type: "textbox",
    left: 200,
    top: 300,
    html: "텍스트 입력",
  };
  getCurrentPage().objects.push(obj);
  save();
  spawnTextbox(obj);
};

function spawnTextbox(obj) {
  const box = createEl("div", "textbox");
  box.dataset.id = obj.id;
  box.style.left = obj.left + "px";
  box.style.top = obj.top + "px";
  box.contentEditable = "true";
  box.innerHTML = obj.html;

  box.oninput = () => {
    obj.html = box.innerHTML;
    save();
  };

  objectLayer.appendChild(box);

  enableDrag(box);
}

/* ========= 오브젝트 드래그 ========= */

function enableDrag(el) {
  let dragging = false;
  let offsetX = 0;
  let offsetY = 0;

  el.addEventListener("mousedown", (e) => {
    if (e.target.classList.contains("resize-handle")) return;
    dragging = true;
    const r = el.getBoundingClientRect();
    offsetX = e.clientX - r.left;
    offsetY = e.clientY - r.top;

    // 선택 표시
    $all(".image-wrapper").forEach((w) => w.classList.remove("selected"));
    if (el.classList.contains("image-wrapper")) el.classList.add("selected");

    e.preventDefault();
  });

  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const nr = noteArea.getBoundingClientRect();
    let x = e.clientX - nr.left - offsetX;
    let y = e.clientY - nr.top - offsetY;
    el.style.left = x + "px";
    el.style.top = y + "px";
  });

  window.addEventListener("mouseup", () => {
    if (dragging) {
      dragging = false;
      saveObjects();
    }
  });
}

/* ========= 이미지 리사이즈 ========= */

function enableResize(wrap, img, handle) {
  let resizing = false;

  handle.addEventListener("mousedown", (e) => {
    resizing = true;
    e.stopPropagation();
  });

  window.addEventListener("mousemove", (e) => {
    if (!resizing) return;
    const nr = noteArea.getBoundingClientRect();
    const left = parseFloat(wrap.style.left);
    const top = parseFloat(wrap.style.top);

    const width = e.clientX - nr.left - left;
    img.style.width = Math.max(40, width) + "px";
  });

  window.addEventListener("mouseup", () => {
    if (resizing) {
      resizing = false;
      saveObjects();
    }
  });
}

/* ========= 오브젝트 저장 ========= */

function saveObjects() {
  const page = getCurrentPage();
  const objs = [];

  // 이미지
  $all(".image-wrapper").forEach((wrap) => {
    const img = wrap.querySelector("img");
    objs.push({
      id: wrap.dataset.id,
      type: "image",
      src: img.src,
      left: parseFloat(wrap.style.left),
      top: parseFloat(wrap.style.top),
      width: parseFloat(img.style.width),
    });
  });

  // 텍스트 박스
  $all(".textbox").forEach((box) => {
    objs.push({
      id: box.dataset.id,
      type: "textbox",
      left: parseFloat(box.style.left),
      top: parseFloat(box.style.top),
      html: box.innerHTML,
    });
  });

  page.objects = objs;
  save();
}

/* ========= PDF 삽입 ========= */

$("#uploadPdfBtn").onclick = () => $("#pdfInput").click();

$("#pdfInput").onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const buffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
    const page = await pdf.getPage(1);

    const rect = noteArea.getBoundingClientRect();
    const vp = page.getViewport({ scale: rect.width / page.getViewport({ scale: 1 }).width });

    const temp = document.createElement("canvas");
    temp.width = vp.width;
    temp.height = vp.height;
    const ctx = temp.getContext("2d");

    await page.render({ canvasContext: ctx, viewport: vp }).promise;

    const url = temp.toDataURL();
    noteArea.style.backgroundImage = `url(${url})`;
    noteArea.style.backgroundSize = "contain";
    noteArea.style.backgroundRepeat = "no-repeat";
    noteArea.style.backgroundPosition = "top center";

    toast("PDF 삽입 완료!");
  } catch (err) {
    console.error(err);
    toast("PDF 오류");
  }

  e.target.value = "";
};

/* ========= 보기 (배경/패턴/줌) ========= */

$all(".bg-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    const bg = btn.dataset.bg;
    const p = getCurrentPage();
    p.background = bg;
    save();
    loadPageToUI();
  })
);

$all(".pattern-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    const pt = btn.dataset.pattern;
    const p = getCurrentPage();
    p.pattern = pt;
    save();
    loadPageToUI();
  })
);

$("#zoomSlider").oninput = () => {
  const v = $("#zoomSlider").value;
  const scale = v / 100;
  $("#zoomLabel").textContent = v + "%";

  const p = getCurrentPage();
  p.zoom = scale;
  save();
  loadPageToUI();
};

$("#toggleInkLayer").onchange = () => {
  inkCanvas.style.display = $("#toggleInkLayer").checked ? "block" : "none";
};

$("#toggleTextLayer").onchange = () => {
  textEditor.style.display = $("#toggleTextLayer").checked ? "block" : "none";
};

$("#toggleImageLayer").onchange = () => {
  objectLayer.style.display = $("#toggleImageLayer").checked ? "block" : "none";
};

/* ========= 리본 탭 클릭 ========= */

$all(".menu-tab").forEach((btn) =>
  btn.addEventListener("click", () => {
    $all(".menu-tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    const tab = btn.dataset.tab;
    $all(".ribbon-content").forEach((sec) =>
      sec.classList.toggle("hidden", sec.id !== "tab-" + tab)
    );
  })
);

/* ========= 파일 탭 ========= */

$("#exportPageImageBtn").onclick = () => {
  toast("html2canvas 연동 시 페이지 저장 가능!");
};

/* ========= AI ========= */

$("#aiSummaryBtn").onclick = () => {
  toast("AI 기능은 서버 연동 후 사용 가능!");
};

/* ========= 초기 실행 ========= */

load();
renderSections();
renderPages();
loadPageToUI();
updateInkEvents();

toast("Minji Notebook ✨ 준비 완료!");
