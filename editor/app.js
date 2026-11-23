"use strict";

/* ------------------------------------------------------------------ state */
const DEFAULTS = () => ({
  rotation: 0, flipH: false, flipV: false, aspect: null,
  exposure: 0, contrast: 0, highlights: 0, shadows: 0, saturation: 0, warmth: 0,
  filter: "none", layers: [],
  curve: [0, 0.25, 0.5, 0.75, 1],
  hsl: Array.from({ length: 8 }, () => ({ h: 0, s: 0, l: 0 }))
});

let state = DEFAULTS();
let source = null;            // HTMLImageElement / ImageBitmap
let undoStack = [], redoStack = [];
let comparing = false;
let activeTab = "Adjust";
let brushColor = "#ff3b30";
let brushSize = 18;           // in preview pixels
let tool = "pen";
let liveStroke = null;

const FILTERS = {
  none:     [1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,1,0],
  mono:     [.33,.33,.33,0,0, .33,.33,.33,0,0, .33,.33,.33,0,0, 0,0,0,1,0],
  noir:     [1.55,0,0,0,-42, 0,1.55,0,0,-42, 0,0,1.55,0,-42, 0,0,0,1,0],
  warm:     [1.12,0,0,0,12, 0,1.04,0,0,2, 0,0,.92,0,-8, 0,0,0,1,0],
  cool:     [.92,0,0,0,-6, 0,1.02,0,0,2, 0,0,1.14,0,12, 0,0,0,1,0],
  vivid:    [1.25,0,0,0,-18, 0,1.25,0,0,-18, 0,0,1.25,0,-18, 0,0,0,1,0],
  fade:     [.88,0,0,0,22, 0,.88,0,0,22, 0,0,.9,0,20, 0,0,0,1,0],
  sepia:    [.393,.769,.189,0,0, .349,.686,.168,0,0, .272,.534,.131,0,0, 0,0,0,1,0],
  matte:    [.82,0,0,0,34, 0,.82,0,0,34, 0,0,.84,0,34, 0,0,0,1,0]
};

/* ------------------------------------------------------------------ helpers */
const $ = id => document.getElementById(id);
const view = $("view");
const ctx = view.getContext("2d", { willReadFrequently: true });
let toastTimer = 0;
function toast(msg){
  const t = $("toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
}
function pushUndo(){
  undoStack.push(JSON.stringify(state));
  if (undoStack.length > 60) undoStack.shift();
  redoStack = [];
  refreshHistoryButtons();
}
function refreshHistoryButtons(){
  $("undoBtn").disabled = undoStack.length === 0;
  $("redoBtn").disabled = redoStack.length === 0;
  $("saveBtn").disabled = !source;
  $("cmpBtn").disabled = !source;
}
function undo(){
  if (!undoStack.length) return;
  redoStack.push(JSON.stringify(state));
  state = JSON.parse(undoStack.pop());
  buildPanel(); schedule();
  refreshHistoryButtons();
}
function redo(){
  if (!redoStack.length) return;
  undoStack.push(JSON.stringify(state));
  state = JSON.parse(redoStack.pop());
  buildPanel(); schedule();
  refreshHistoryButtons();
}

/* ------------------------------------------------------------------ pipeline */
function geometry(w, h){
  let W = state.rotation % 180 === 0 ? w : h;
  let H = state.rotation % 180 === 0 ? h : w;
  let cw = W, ch = H, cx = 0, cy = 0;
  if (state.aspect){
    const a = state.aspect;
    if (W / H > a){ cw = Math.round(H * a); cx = Math.round((W - cw) / 2); }
    else { ch = Math.round(W / a); cy = Math.round((H - ch) / 2); }
  }
  return { W, H, cw, ch, cx, cy };
}

function drawBase(target, src, maxEdge){
  const w = src.width, h = src.height;
  const g = geometry(w, h);
  let scale = 1;
  if (maxEdge && Math.max(g.cw, g.ch) > maxEdge) scale = maxEdge / Math.max(g.cw, g.ch);
  target.width = Math.max(1, Math.round(g.cw * scale));
  target.height = Math.max(1, Math.round(g.ch * scale));
  const c = target.getContext("2d", { willReadFrequently: true });
  c.save();
  c.scale(scale, scale);
  c.translate(-g.cx, -g.cy);
  c.translate(g.W / 2, g.H / 2);
  c.rotate(state.rotation * Math.PI / 180);
  c.scale(state.flipH ? -1 : 1, state.flipV ? -1 : 1);
  c.translate(-w / 2, -h / 2);
  c.drawImage(src, 0, 0);
  c.restore();
  return c;
}


const HSL_CHANNELS = [
  ["Red", 0], ["Orange", 30], ["Yellow", 60], ["Green", 120],
  ["Aqua", 180], ["Blue", 240], ["Purple", 285], ["Magenta", 320]
];

function catmull(p0, p1, p2, p3, t){
  const t2 = t * t, t3 = t2 * t;
  return 0.5 * ((2 * p1) + (-p0 + p2) * t +
    (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
}

function curveLut(points){
  const lut = new Uint8ClampedArray(256);
  const n = points.length;
  for (let i = 0; i < 256; i++){
    const t = (i / 255) * (n - 1);
    const idx = Math.min(n - 2, Math.max(0, Math.floor(t)));
    const f = t - idx;
    const p0 = points[Math.max(0, idx - 1)];
    const p1 = points[idx];
    const p2 = points[idx + 1];
    const p3 = points[Math.min(n - 1, idx + 2)];
    lut[i] = Math.round(Math.min(1, Math.max(0, catmull(p0, p1, p2, p3, f))) * 255);
  }
  return lut;
}

function isNeutralCurve(c){
  return c.length === 5 && Math.abs(c[0]) < 1e-4 && Math.abs(c[1] - .25) < 1e-4 &&
    Math.abs(c[2] - .5) < 1e-4 && Math.abs(c[3] - .75) < 1e-4 && Math.abs(c[4] - 1) < 1e-4;
}

function rgbToHsv(r, g, b){
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d > 1){
    if (mx === r) h = 60 * (((g - b) / d) % 6);
    else if (mx === g) h = 60 * (((b - r) / d) + 2);
    else h = 60 * (((r - g) / d) + 4);
  }
  if (h < 0) h += 360;
  return [h, mx <= 0 ? 0 : d / mx, mx / 255];
}

function hsvToRgb(h, s, v){
  const c = v * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = v - c;
  let r = 0, g = 0, b = 0;
  if (h < 60){ r = c; g = x; }
  else if (h < 120){ r = x; g = c; }
  else if (h < 180){ g = c; b = x; }
  else if (h < 240){ g = x; b = c; }
  else if (h < 300){ r = x; b = c; }
  else { r = c; b = x; }
  return [(r + m) * 255, (g + m) * 255, (b + m) * 255];
}

function bandWeight(hue, centre){
  let d = Math.abs(hue - centre);
  if (d > 180) d = 360 - d;
  return Math.min(1, Math.max(0, 1 - d / 45));
}

function applyColour(canvas){
  const m = FILTERS[state.filter] || FILTERS.none;
  const exp = 1 + state.exposure * 0.9;
  const con = 1 + state.contrast;
  const off = (1 - con) * 127.5;
  const satK = 1 + state.saturation;
  const warm = state.warmth * 45;
  const hi = state.highlights, sh = state.shadows;
  const lut = isNeutralCurve(state.curve) ? null : curveLut(state.curve);
  const hslOn = state.hsl.some(c => c.h || c.s || c.l);
  const img = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height);
  const d = img.data;
  for (let i = 0; i < d.length; i += 4){
    let r = d[i], g = d[i+1], b = d[i+2];
    // preset matrix
    const nr = m[0]*r + m[1]*g + m[2]*b + m[4];
    const ng = m[5]*r + m[6]*g + m[7]*b + m[9];
    const nb = m[10]*r + m[11]*g + m[12]*b + m[14];
    r = nr; g = ng; b = nb;
    // exposure + contrast
    r = r * exp * con + off; g = g * exp * con + off; b = b * exp * con + off;
    // saturation
    if (satK !== 1){
      const l = 0.299*r + 0.587*g + 0.114*b;
      r = l + (r - l) * satK; g = l + (g - l) * satK; b = l + (b - l) * satK;
    }
    // highlights / shadows
    if (hi || sh){
      const lum = (0.299*r + 0.587*g + 0.114*b) / 255;
      let f = 0;
      if (sh) f += sh * (1-lum) * (1-lum) * 100;
      if (hi) f += hi * lum * lum * 100;
      r += f; g += f; b += f;
    }
    // warmth
    if (warm){ r += warm; b -= warm; }
    // tone curve (master)
    if (lut){
      r = lut[Math.max(0, Math.min(255, r | 0))];
      g = lut[Math.max(0, Math.min(255, g | 0))];
      b = lut[Math.max(0, Math.min(255, b | 0))];
    }
    // eight-channel HSL mixer
    if (hslOn){
      const clamped = [Math.min(255, Math.max(0, r)), Math.min(255, Math.max(0, g)), Math.min(255, Math.max(0, b))];
      const hsv = rgbToHsv(clamped[0], clamped[1], clamped[2]);
      if (hsv[2] > 0.02){
        let dHue = 0, sScale = 1, vScale = 1, wSum = 0;
        for (let ci = 0; ci < 8; ci++){
          const shift = state.hsl[ci];
          if (!shift.h && !shift.s && !shift.l) continue;
          const w = bandWeight(hsv[0], HSL_CHANNELS[ci][1]);
          if (w <= 0) continue;
          wSum += w; dHue += w * shift.h * 30; sScale += w * shift.s; vScale += w * shift.l;
        }
        if (wSum > 0){
          const nh = (hsv[0] + dHue / wSum + 360) % 360;
          const ns = Math.min(1, Math.max(0, hsv[1] * sScale));
          const nv = Math.min(1, Math.max(0, hsv[2] * vScale));
          const out = hsvToRgb(nh, ns, nv);
          r = out[0]; g = out[1]; b = out[2];
        }
      }
    }
    d[i]   = r < 0 ? 0 : r > 255 ? 255 : r;
    d[i+1] = g < 0 ? 0 : g > 255 ? 255 : g;
    d[i+2] = b < 0 ? 0 : b > 255 ? 255 : b;
  }
  canvas.getContext("2d").putImageData(img, 0, 0);
}

function drawLayers(canvas){
  const layers = liveStroke ? state.layers.concat([liveStroke]) : state.layers;
  if (!layers.length) return;
  const c = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  for (const layer of layers){
    if (layer.type === "stroke") drawStroke(c, layer, W, H);
    if (layer.type === "text"){
      c.save();
      c.fillStyle = layer.color;
      c.font = "700 " + Math.round(layer.size * H) + "px -apple-system,Segoe UI,Roboto,sans-serif";
      c.shadowColor = "rgba(0,0,0,.55)"; c.shadowBlur = 6; c.shadowOffsetY = 2;
      c.fillText(layer.text, layer.x * W, layer.y * H);
      c.restore();
    }
  }
}

function strokePath(layer, W, H){
  const p = new Path2D();
  const pts = layer.points;
  p.moveTo(pts[0][0] * W, pts[0][1] * H);
  for (let i = 1; i < pts.length; i++) p.lineTo(pts[i][0] * W, pts[i][1] * H);
  return p;
}

function drawStroke(c, layer, W, H){
  const path = strokePath(layer, W, H);
  const width = Math.max(2, layer.width * Math.min(W, H));
  if (layer.mode === "pen" || layer.mode === "blackout" || layer.mode === "highlight"){
    c.save();
    c.lineJoin = c.lineCap = "round";
    c.lineWidth = layer.mode === "highlight" ? width * 2.2 : width;
    c.strokeStyle = layer.mode === "blackout" ? "#000" : layer.color;
    c.globalAlpha = layer.mode === "highlight" ? .38 : 1;
    c.stroke(path);
    c.restore();
    return;
  }
  // pixelate / blur: work on the covered area only
  const box = strokeBounds(layer, W, H, width);
  if (!box || box.w < 3 || box.h < 3) return;
  const patch = document.createElement("canvas");
  patch.width = Math.max(1, Math.round(box.w));
  patch.height = Math.max(1, Math.round(box.h));
  patch.getContext("2d").drawImage(c.canvas, box.x, box.y, box.w, box.h, 0, 0, patch.width, patch.height);

  const effect = document.createElement("canvas");
  effect.width = patch.width; effect.height = patch.height;
  const ec = effect.getContext("2d");
  if (layer.mode === "pixelate"){
    const block = Math.max(6, Math.round(Math.min(patch.width, patch.height) / 14));
    const small = document.createElement("canvas");
    small.width = Math.max(1, Math.round(patch.width / block));
    small.height = Math.max(1, Math.round(patch.height / block));
    small.getContext("2d").drawImage(patch, 0, 0, small.width, small.height);
    ec.imageSmoothingEnabled = false;
    ec.drawImage(small, 0, 0, patch.width, patch.height);
  } else {
    const small = document.createElement("canvas");
    small.width = Math.max(1, Math.round(patch.width / 12));
    small.height = Math.max(1, Math.round(patch.height / 12));
    small.getContext("2d").drawImage(patch, 0, 0, small.width, small.height);
    ec.drawImage(small, 0, 0, patch.width, patch.height);
  }
  const pattern = c.createPattern(effect, "no-repeat");
  if (!pattern || !pattern.setTransform) return;
  pattern.setTransform(new DOMMatrix([1, 0, 0, 1, box.x, box.y]));
  c.save();
  c.lineJoin = c.lineCap = "round";
  c.lineWidth = width * 1.6;
  c.strokeStyle = pattern;
  c.stroke(path);
  c.restore();
}

function strokeBounds(layer, W, H, width){
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
  for (const [x, y] of layer.points){
    const px = x * W, py = y * H;
    if (px < minX) minX = px;
    if (py < minY) minY = py;
    if (px > maxX) maxX = px;
    if (py > maxY) maxY = py;
  }
  const pad = width * 0.9;
  minX = Math.max(0, Math.floor(minX - pad));
  minY = Math.max(0, Math.floor(minY - pad));
  maxX = Math.min(W, Math.ceil(maxX + pad));
  maxY = Math.min(H, Math.ceil(maxY + pad));
  if (maxX <= minX || maxY <= minY) return null;
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

function renderTo(canvas, src, maxEdge){
  drawBase(canvas, src, maxEdge);
  applyColour(canvas);
  drawLayers(canvas);
  return canvas;
}

/* ------------------------------------------------------------------ view */
let renderPending = false;
function schedule(){
  if (renderPending || !source) return;
  renderPending = true;
  requestAnimationFrame(() => {
    renderPending = false;
    const out = renderTo(view, source, 1400);
    view.hidden = false;
    $("drop").hidden = true;
    $("dock").hidden = false;
    $("hint").hidden = true;
  });
}

/* ------------------------------------------------------------------ load */
function loadFile(file){
  if (!file || !file.type.startsWith("image/")) return;
  const url = URL.createObjectURL(file);
  const img = new Image();
  img.onload = () => {
    source = img;
    state = DEFAULTS();
    undoStack = []; redoStack = [];
    activeTab = "Adjust";
    buildTabs(); buildPanel(); schedule(); refreshHistoryButtons();
    URL.revokeObjectURL(url);
    toast("Loaded " + img.width + " × " + img.height);
  };
  img.onerror = () => toast("That file could not be opened");
  img.src = url;
}

$("pickBtn").onclick = () => $("file").click();
$("openBtn").onclick = () => $("file").click();
$("file").onchange = e => loadFile(e.target.files[0]);
$("pasteBtn").onclick = async () => {
  try {
    const items = await navigator.clipboard.read();
    for (const item of items){
      const type = item.types.find(t => t.startsWith("image/"));
      if (type){ loadFile(new File([await item.getType(type)], "pasted.png", { type })); return; }
    }
    toast("No image on the clipboard");
  } catch (e){ toast("Clipboard access was blocked — drag the image instead"); }
};
document.addEventListener("paste", e => {
  const item = [...(e.clipboardData?.items || [])].find(i => i.type.startsWith("image/"));
  if (item) loadFile(item.getAsFile());
});
["dragover","dragenter"].forEach(ev => $("stage").addEventListener(ev, e => e.preventDefault()));
$("stage").addEventListener("drop", e => {
  e.preventDefault();
  const f = e.dataTransfer.files[0];
  if (f) loadFile(f);
});

/* ------------------------------------------------------------------ ui */
const TABS = ["Crop","Adjust","Curves","HSL","Filters","Markup","Export"];
function buildTabs(){
  const wrap = $("tabs");
  wrap.innerHTML = "";
  TABS.forEach(name => {
    const b = document.createElement("button");
    b.className = "tab" + (name === activeTab ? " sel" : "");
    b.textContent = name;
    b.onclick = () => { activeTab = name; buildTabs(); buildPanel(); };
    wrap.appendChild(b);
  });
}

function slider(label, key, min, max, step, fmt){
  const wrap = document.createElement("div");
  wrap.className = "slider";
  const lbl = document.createElement("div");
  lbl.className = "lbl";
  const v = state[key];
  lbl.innerHTML = "<span>" + label + "</span><b>" + (fmt ? fmt(v) : Math.round(v * 100)) + "</b>";
  const input = document.createElement("input");
  input.type = "range"; input.min = min; input.max = max; input.step = step; input.value = v;
  input.onpointerdown = () => pushUndo();
  input.oninput = () => {
    state[key] = parseFloat(input.value);
    lbl.querySelector("b").textContent = fmt ? fmt(state[key]) : Math.round(state[key] * 100);
    schedule();
  };
  lbl.onclick = () => {
    pushUndo(); state[key] = 0; input.value = 0;
    lbl.querySelector("b").textContent = fmt ? fmt(0) : "0";
    schedule();
  };
  wrap.append(lbl, input);
  return wrap;
}

function chipRow(items, current, onPick){
  const row = document.createElement("div");
  row.className = "chips";
  items.forEach(([value, label]) => {
    const b = document.createElement("button");
    b.className = "chip" + (current === value ? " sel" : "");
    b.textContent = label;
    b.onclick = () => { pushUndo(); onPick(value); buildPanel(); schedule(); };
    row.appendChild(b);
  });
  return row;
}


function drawCurve(cv){
  const c = cv.getContext("2d");
  const W = cv.width, H = cv.height;
  c.clearRect(0, 0, W, H);
  c.fillStyle = "#0a0a0c";
  c.fillRect(0, 0, W, H);
  c.strokeStyle = "#2a2a2e";
  c.lineWidth = 1;
  for (let i = 1; i < 4; i++){
    c.beginPath(); c.moveTo((W * i) / 4, 0); c.lineTo((W * i) / 4, H); c.stroke();
    c.beginPath(); c.moveTo(0, (H * i) / 4); c.lineTo(W, (H * i) / 4); c.stroke();
  }
  const lut = curveLut(state.curve);
  c.strokeStyle = "#00e0b2";
  c.lineWidth = 2;
  c.beginPath();
  for (let i = 0; i < 256; i++){
    const x = (W * i) / 255;
    const y = H - (lut[i] / 255) * H;
    if (i === 0) c.moveTo(x, y); else c.lineTo(x, y);
  }
  c.stroke();
  state.curve.forEach((v, i) => {
    const x = (W * i) / (state.curve.length - 1);
    const y = H - v * H;
    c.beginPath(); c.arc(x, y, 6, 0, Math.PI * 2);
    c.fillStyle = "#fff"; c.fill();
    c.beginPath(); c.arc(x, y, 3.4, 0, Math.PI * 2);
    c.fillStyle = "#00e0b2"; c.fill();
  });
}

function attachCurveDrag(cv){
  let idx = -1;
  const pointFrom = ev => {
    const r = cv.getBoundingClientRect();
    const x = (ev.clientX - r.left) / r.width;
    const y = (ev.clientY - r.top) / r.height;
    return [Math.min(1, Math.max(0, x)), Math.min(1, Math.max(0, 1 - y))];
  };
  cv.addEventListener("pointerdown", ev => {
    const [x] = pointFrom(ev);
    idx = Math.round(x * (state.curve.length - 1));
    pushUndo();
    cv.setPointerCapture(ev.pointerId);
  });
  cv.addEventListener("pointermove", ev => {
    if (idx < 0) return;
    const [, y] = pointFrom(ev);
    state.curve[idx] = y;
    drawCurve(cv);
    schedule();
  });
  ["pointerup", "pointercancel"].forEach(e => cv.addEventListener(e, () => { idx = -1; }));
}

function hslSlider(label, channel, prop){
  const wrap = document.createElement("div");
  wrap.className = "slider";
  const lbl = document.createElement("div");
  lbl.className = "lbl";
  const v = state.hsl[channel][prop];
  lbl.innerHTML = "<span>" + label + "</span><b>" + Math.round(v * 100) + "</b>";
  const input = document.createElement("input");
  input.type = "range"; input.min = -1; input.max = 1; input.step = 0.01; input.value = v;
  input.onpointerdown = () => pushUndo();
  input.oninput = () => {
    state.hsl[channel][prop] = parseFloat(input.value);
    lbl.querySelector("b").textContent = Math.round(state.hsl[channel][prop] * 100);
    schedule();
  };
  lbl.onclick = () => {
    pushUndo(); state.hsl[channel][prop] = 0; input.value = 0;
    lbl.querySelector("b").textContent = "0"; schedule();
  };
  wrap.append(lbl, input);
  return wrap;
}

let hslChannel = 0;

function buildPanel(){
  const p = $("panel");
  p.innerHTML = "";
  if (activeTab === "Crop"){
    p.appendChild(chipRow([[0,"Rotate 0°"],[90,"90°"],[180,"180°"],[270,"270°"]], state.rotation, v => { state.rotation = v; }));
    const flips = document.createElement("div");
    flips.className = "chips";
    [["H","flipH"],["V","flipV"]].forEach(([label, key]) => {
      const b = document.createElement("button");
      b.className = "chip" + (state[key] ? " sel" : "");
      b.textContent = "Flip " + label;
      b.onclick = () => { pushUndo(); state[key] = !state[key]; buildPanel(); schedule(); };
      flips.appendChild(b);
    });
    p.appendChild(flips);
    p.appendChild(chipRow([[null,"Free"],[1,"1:1"],[.8,"4:5"],[16/9,"16:9"],[1.5,"3:2"]], state.aspect, v => { state.aspect = v; }));
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Crop here is a centred aspect crop, same as the app's presets. Rotation and flips are lossless.";
    p.appendChild(note);
  }
  if (activeTab === "Adjust"){
    p.appendChild(slider("Exposure","exposure",-1,1,.01));
    p.appendChild(slider("Contrast","contrast",-1,1,.01));
    p.appendChild(slider("Highlights","highlights",-1,1,.01));
    p.appendChild(slider("Shadows","shadows",-1,1,.01));
    p.appendChild(slider("Saturation","saturation",-1,1,.01));
    p.appendChild(slider("Warmth","warmth",-1,1,.01));
  }
  if (activeTab === "Curves"){
    const wrap = document.createElement("div");
    wrap.className = "curve-wrap";
    const cv = document.createElement("canvas");
    cv.width = 300; cv.height = 170; cv.className = "curve-canvas";
    wrap.appendChild(cv);
    p.appendChild(wrap);
    drawCurve(cv);
    attachCurveDrag(cv);
    const row = document.createElement("div");
    row.className = "chips";
    const reset = document.createElement("button");
    reset.className = "chip"; reset.textContent = "Reset curve";
    reset.onclick = () => { pushUndo(); state.curve = [0, .25, .5, .75, 1]; buildPanel(); schedule(); };
    row.appendChild(reset);
    p.appendChild(row);
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Drag a point up or down. The curve is baked into a 256-step lookup and applied in the same pass as the sliders.";
    p.appendChild(note);
  }
  if (activeTab === "HSL"){
    const row = document.createElement("div");
    row.className = "chips";
    HSL_CHANNELS.forEach(([name], i) => {
      const b = document.createElement("button");
      b.className = "chip" + (hslChannel === i ? " sel" : "");
      b.textContent = name;
      b.onclick = () => { hslChannel = i; buildPanel(); };
      row.appendChild(b);
    });
    p.appendChild(row);
    p.appendChild(hslSlider("Hue", hslChannel, "h"));
    p.appendChild(hslSlider("Saturation", hslChannel, "s"));
    p.appendChild(hslSlider("Luminance", hslChannel, "l"));
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Selective colour: only pixels near this hue are affected, so a blue sky can change without touching skin or walls.";
    p.appendChild(note);
  }
  if (activeTab === "Filters"){
    const names = [["none","Original"],["mono","Mono"],["noir","Noir"],["warm","Warm"],["cool","Cool"],["vivid","Vivid"],["fade","Fade"],["sepia","Sepia"],["matte","Matte"]];
    p.appendChild(chipRow(names, state.filter, v => { state.filter = v; }));
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Presets are colour matrices applied in the same pass as the sliders, so they stack.";
    p.appendChild(note);
  }
  if (activeTab === "Markup"){
    p.appendChild(chipRow([["pen","Pen"],["highlight","Highlighter"],["pixelate","Pixelate"],["blackout","Blackout"]], tool, v => { tool = v; }));
    const colors = ["#ff3b30","#00e0b2","#3b82f6","#ffd60a","#ffffff","#000000"];
    const row = document.createElement("div");
    row.className = "chips";
    colors.forEach(c => {
      const b = document.createElement("button");
      b.className = "chip" + (brushColor === c ? " sel" : "");
      b.style.background = c; b.style.width = "30px"; b.style.height = "30px"; b.style.padding = "0"; b.style.borderRadius = "50%";
      b.onclick = () => { brushColor = c; buildPanel(); };
      row.appendChild(b);
    });
    p.appendChild(row);
    p.appendChild(slider("Brush size","_brush",4,60,1,v => Math.round(v)));
    const clear = document.createElement("button");
    clear.className = "chip";
    clear.textContent = "Clear markup";
    clear.onclick = () => { pushUndo(); state.layers = []; buildPanel(); schedule(); };
    p.appendChild(clear);
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Draw on the photo above. Pixelate and blackout are applied to the pixels under the stroke.";
    p.appendChild(note);
  }
  if (activeTab === "Export"){
    const f = document.createElement("div");
    f.className = "chips";
    ["image/jpeg","image/png","image/webp"].forEach((mime, i) => {
      const b = document.createElement("button");
      b.className = "chip" + (exportMime === mime ? " sel" : "");
      b.textContent = mime.split("/")[1].toUpperCase();
      b.onclick = () => { exportMime = mime; buildPanel(); };
      f.appendChild(b);
    });
    p.appendChild(f);
    p.appendChild(slider("Quality","_quality",10,100,1,v => Math.round(v)));
    const btn = document.createElement("button");
    btn.className = "save"; btn.textContent = "Save image";
    btn.onclick = doExport;
    p.appendChild(btn);
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Exported at full resolution. Re-encoding through canvas drops EXIF and GPS automatically — the same default the app uses.";
    p.appendChild(note);
  }
  // brush/quality pseudo-sliders need their own binding
  if (state._brush === undefined) state._brush = brushSize;
  if (state._quality === undefined) state._quality = 92;
}

let exportMime = "image/jpeg";
let exportQuality = 92;

/* the two pseudo sliders above reuse `slider()`, so map them onto globals */
const rawSlider = slider;
slider = function(label, key, min, max, step, fmt){
  if (key === "_brush"){
    const wrap = rawSlider(label, "_brush", min, max, step, fmt);
    const input = wrap.querySelector("input");
    input.value = brushSize;
    wrap.querySelector("b").textContent = Math.round(brushSize);
    input.oninput = () => { brushSize = parseFloat(input.value); wrap.querySelector("b").textContent = Math.round(brushSize); };
    wrap.querySelector(".lbl").onclick = () => { brushSize = 18; input.value = 18; wrap.querySelector("b").textContent = "18"; };
    return wrap;
  }
  if (key === "_quality"){
    const wrap = rawSlider(label, "_quality", min, max, step, fmt);
    const input = wrap.querySelector("input");
    input.value = exportQuality;
    wrap.querySelector("b").textContent = exportQuality;
    input.oninput = () => { exportQuality = parseFloat(input.value); wrap.querySelector("b").textContent = exportQuality; };
    return wrap;
  }
  return rawSlider(label, key, min, max, step, fmt);
};

/* ------------------------------------------------------------------ drawing */
let drawing = false;
function canvasPoint(ev){
  const rect = view.getBoundingClientRect();
  return [ (ev.clientX - rect.left) / rect.width, (ev.clientY - rect.top) / rect.height ];
}
view.addEventListener("pointerdown", ev => {
  if (!source || activeTab !== "Markup") return;
  drawing = true;
  pushUndo();
  liveStroke = { type:"stroke", mode:tool, color:brushColor, width: brushSize / 900, points: [canvasPoint(ev)] };
  view.setPointerCapture(ev.pointerId);
});
view.addEventListener("pointermove", ev => {
  if (!drawing || !liveStroke) return;
  liveStroke.points.push(canvasPoint(ev));
  schedule();
});
view.addEventListener("pointerup", () => {
  if (!drawing || !liveStroke) return;
  drawing = false;
  if (liveStroke.points.length > 1) state.layers = state.layers.concat([liveStroke]);
  liveStroke = null;
  schedule();
});

/* compare */
const cmp = $("cmpBtn");
cmp.addEventListener("pointerdown", () => { comparing = true; renderCompare(); });
["pointerup","pointerleave","pointercancel"].forEach(e => cmp.addEventListener(e, () => { comparing = false; schedule(); }));
function renderCompare(){
  if (!source) return;
  drawBase(view, source, 1400);
  view.hidden = false;
}

/* ------------------------------------------------------------------ export */
function doExport(){
  if (!source) return;
  $("busy").hidden = false;
  setTimeout(() => {
    const full = document.createElement("canvas");
    renderTo(full, source, Math.max(source.width, source.height));
    full.toBlob(blob => {
      $("busy").hidden = true;
      if (!blob){ toast("Export failed"); return; }
      const a = document.createElement("a");
      const ext = exportMime === "image/png" ? "png" : exportMime === "image/webp" ? "webp" : "jpg";
      a.href = URL.createObjectURL(blob);
      a.download = "Nijatva_" + Date.now() + "." + ext;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      toast("Saved " + (blob.size / 1024).toFixed(0) + " KB");
    }, exportMime, exportQuality / 100);
  }, 30);
}

/* ------------------------------------------------------------------ boot */
$("undoBtn").onclick = undo;
$("redoBtn").onclick = redo;
$("saveBtn").onclick = doExport;
buildTabs(); refreshHistoryButtons();
if ("serviceWorker" in navigator && location.protocol.startsWith("http")){
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}
