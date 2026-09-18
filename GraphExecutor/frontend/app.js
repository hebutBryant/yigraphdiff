// GraphExecutor 前端应用
// 输入提示词 -> 预测场景图 -> 渲染 graph + 布局图像

const API = "/api/v1";
let currentGraph = null;   // 当前场景图 (SceneGraphOutput)

// ---- DOM 辅助 ----
const $ = (sel) => document.querySelector(sel);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "html") n.innerHTML = v;
    else n.setAttribute(k, v);
  }
  kids.forEach((c) => n.append(c));
  return n;
};

function toast(msg, isErr = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (isErr ? " err" : "");
  setTimeout(() => (t.className = "toast"), 2600);
}

// ---- API 调用 ----
async function apiJSON(path, body) {
  const res = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `请求失败 (${res.status})`);
  }
  return res.json();
}

async function apiBlob(path, body) {
  const res = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `请求失败 (${res.status})`);
  }
  return res.blob();
}

// 将 SceneGraphOutput 转为 SceneGraphInput（供 /visualize 等接口复用）
function graphToInput(g) {
  return {
    high_level_description: g.high_level_description,
    style_description: g.style_description || "",
    background: g.background || "",
    width: g.width,
    height: g.height,
    elements: g.elements.map((n) => ({
      id: n.id, type: n.type, bbox: n.bbox, desc: n.desc,
      control_extend: n.control_extend || 0,
    })),
    edges: g.edges.map((e) => ({
      id: e.id, source: e.source, target: e.target, type: e.type,
      strength: e.strength, direction: e.direction, phase: e.phase,
      mode: e.mode, priority: e.priority, relation_phrase: e.relation_phrase || "",
    })),
  };
}

// ---- 边类型 -> 颜色分类 ----
const EDGE_CATEGORY = {
  spatial: "spatial", left_of: "spatial", right_of: "spatial", above: "spatial",
  below: "spatial", near: "spatial", next_to: "spatial",
  contact: "contact", serving: "contact", holding: "contact", placed_on: "contact",
  carrying: "contact", on: "contact", in: "contact",
  gaze_pointing: "gaze", looks_at: "gaze", points_to: "gaze", pointing: "gaze", watching: "gaze",
  reflection: "reflection", reflected_by: "reflection",
  lighting: "lighting", illuminates: "lighting", casts_shadow: "lighting",
  specular_highlight: "lighting",
  negative_attribute: "negative",
};
const CAT_COLOR = {
  spatial: "#38bdf8", contact: "#34d399", gaze: "#fbbf24",
  reflection: "#a78bfa", lighting: "#fb923c", negative: "#f87171",
  default: "#94a3b8",
};
const catOf = (t) => EDGE_CATEGORY[t] || "default";
const colorOf = (t) => CAT_COLOR[catOf(t)] || CAT_COLOR.default;

// ---- 在 SVG 中渲染 graph（按 bbox 位置布局节点）----
function renderGraph(g) {
  const host = $("#graph-view");
  host.innerHTML = "";
  const W = 760, H = 560, pad = 30;
  const sx = (W - 2 * pad) / g.width;
  const sy = (H - 2 * pad) / g.height;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("class", "graph-svg");

  // 箭头定义
  const defs = document.createElementNS(svg.namespaceURI, "defs");
  for (const [cat, col] of Object.entries(CAT_COLOR)) {
    const m = document.createElementNS(svg.namespaceURI, "marker");
    m.setAttribute("id", `arrow-${cat}`);
    m.setAttribute("viewBox", "0 0 10 10");
    m.setAttribute("refX", "9"); m.setAttribute("refY", "5");
    m.setAttribute("markerWidth", "7"); m.setAttribute("markerHeight", "7");
    m.setAttribute("orient", "auto-start-reverse");
    const p = document.createElementNS(svg.namespaceURI, "path");
    p.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
    p.setAttribute("fill", col);
    m.append(p); defs.append(m);
  }
  svg.append(defs);

  // 节点中心坐标
  const center = {};
  g.elements.forEach((n) => {
    const [x1, y1, x2, y2] = n.bbox;
    center[n.id] = { x: pad + ((x1 + x2) / 2) * sx, y: pad + ((y1 + y2) / 2) * sy };
  });

  // 先画边
  g.edges.forEach((e) => {
    const a = center[e.source], b = center[e.target];
    if (!a || !b) return;
    const col = colorOf(e.type);
    const line = document.createElementNS(svg.namespaceURI, "line");
    line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
    line.setAttribute("stroke", col);
    line.setAttribute("stroke-width", 1.2 + (e.strength || 1) * 2.2);
    line.setAttribute("opacity", "0.75");
    line.setAttribute("marker-end", `url(#arrow-${catOf(e.type)})`);
    if (e.mode === "negative") line.setAttribute("stroke-dasharray", "5,4");
    svg.append(line);

    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const lbl = document.createElementNS(svg.namespaceURI, "text");
    lbl.setAttribute("x", mx); lbl.setAttribute("y", my - 4);
    lbl.setAttribute("class", "edge-label");
    lbl.setAttribute("fill", col);
    lbl.textContent = e.type;
    svg.append(lbl);
  });

  // 再画节点
  g.elements.forEach((n) => {
    const c = center[n.id];
    const grp = document.createElementNS(svg.namespaceURI, "g");
    grp.setAttribute("class", "node-grp");

    const circ = document.createElementNS(svg.namespaceURI, "circle");
    circ.setAttribute("cx", c.x); circ.setAttribute("cy", c.y);
    circ.setAttribute("r", 22);
    circ.setAttribute("class", "node-circle");
    grp.append(circ);

    const t = document.createElementNS(svg.namespaceURI, "text");
    t.setAttribute("x", c.x); t.setAttribute("y", c.y + 38);
    t.setAttribute("class", "node-label");
    t.textContent = n.id;
    grp.append(t);

    const title = document.createElementNS(svg.namespaceURI, "title");
    title.textContent = `${n.id} (${n.type})\n${n.desc}`;
    grp.append(title);

    svg.append(grp);
  });

  host.append(svg);
}

// ---- 渲染 bbox 布局预览（HTML 叠加层）----
function renderBBoxPreview(g) {
  const host = $("#bbox-view");
  host.innerHTML = "";
  const stage = el("div", { class: "bbox-stage" });
  const ar = (g.height / g.width) * 100;
  stage.style.paddingBottom = ar + "%";

  g.elements.forEach((n, i) => {
    const [x1, y1, x2, y2] = n.bbox;
    const box = el("div", { class: "bbox" });
    box.style.left = (x1 / g.width) * 100 + "%";
    box.style.top = (y1 / g.height) * 100 + "%";
    box.style.width = ((x2 - x1) / g.width) * 100 + "%";
    box.style.height = ((y2 - y1) / g.height) * 100 + "%";
    const hue = (i * 67) % 360;
    box.style.borderColor = `hsl(${hue},70%,60%)`;
    box.style.background = `hsla(${hue},70%,60%,0.12)`;
    const tag = el("span", { class: "bbox-tag" }, document.createTextNode(n.id));
    tag.style.background = `hsl(${hue},70%,45%)`;
    box.append(tag);
    box.title = n.desc;
    stage.append(box);
  });
  host.append(stage);
}

// ---- 渲染节点/边的明细表 ----
function renderDetails(g) {
  const nodesBox = $("#nodes-detail");
  const edgesBox = $("#edges-detail");
  nodesBox.innerHTML = "";
  edgesBox.innerHTML = "";

  g.elements.forEach((n) => {
    const row = el("div", { class: "detail-item" },
      el("div", { class: "di-head" },
        el("span", { class: "di-id" }, document.createTextNode(n.id)),
        el("span", { class: "di-type" }, document.createTextNode(n.type))),
      el("div", { class: "di-desc" }, document.createTextNode(n.desc || "—")),
      el("div", { class: "di-meta" }, document.createTextNode(`bbox [${n.bbox.join(", ")}]`)));
    nodesBox.append(row);
  });

  if (!g.edges.length) {
    edgesBox.append(el("div", { class: "empty-hint" }, document.createTextNode("无关系边")));
  }
  g.edges.forEach((e) => {
    const col = colorOf(e.type);
    const row = el("div", { class: "detail-item" },
      el("div", { class: "di-head" },
        el("span", { class: "di-dot", style: `background:${col}` }),
        el("span", { class: "di-id" },
          document.createTextNode(`${e.source} → ${e.target}`)),
        el("span", { class: "di-type" }, document.createTextNode(e.type))),
      el("div", { class: "di-meta" },
        document.createTextNode(
          `强度 ${e.strength} · ${e.direction} · ${e.phase} · ${e.mode}`)));
    edgesBox.append(row);
  });
}

// ---- 主流程：预测布局 ----
async function runPredict() {
  const prompt = $("#prompt").value.trim();
  if (!prompt) { toast("请输入提示词", true); return; }

  const width = parseInt($("#width").value, 10) || 1024;
  const height = parseInt($("#height").value, 10) || 1024;

  setBusy(true, "🤖 正在调用 Qwen API 解析场景...");
  try {
    const g = await apiJSON("/predict-layout", { prompt, width, height });
    currentGraph = g;

    setBusy(true, "🎨 正在渲染场景图...");
    await new Promise(r => setTimeout(r, 200)); // 让用户看到状态变化

    $("#empty-state").style.display = "none";
    $("#result").style.display = "flex";

    renderGraph(g);
    renderBBoxPreview(g);
    renderDetails(g);
    updateStats(g);

    setBusy(true, "🖼️  正在生成布局可视化...");
    await loadServerVisualization(g);

    toast(`✅ 已生成：${g.elements.length} 个对象，${g.edges.length} 条关系`);
  } catch (e) {
    console.error("预测失败:", e);
    toast("❌ " + e.message, true);
  } finally {
    setBusy(false);
  }
}

// ---- 调用后端 /visualize 获取 PNG 布局图 ----
async function loadServerVisualization(g) {
  const img = $("#layout-img");
  const type = $("#viz-type").value;
  img.classList.add("loading");
  img.src = ""; // 清空旧图
  $("#img-hint").textContent = "⏳ 正在渲染布局图...";

  try {
    const blob = await apiBlob("/visualize", {
      scene_graph: graphToInput(g),
      visualization_type: type,
      show_labels: true,
    });
    img.src = URL.createObjectURL(blob);
    $("#img-hint").textContent =
      "📊 后端渲染的布局图 (matplotlib)。连接 FLUX 模型后此处将显示生成的图像。";
  } catch (e) {
    console.error("可视化失败:", e);
    $("#img-hint").textContent = "❌ 布局图渲染失败：" + e.message;
  } finally {
    img.classList.remove("loading");
  }
}

// ---- 切换到指定 Tab ----
function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((p) =>
    p.classList.toggle("active", p.id === "panel-" + name));
}

// ---- 轮询任务状态直到完成/失败 ----
async function pollTask(taskId, { interval = 3000, timeout = 600000 } = {}) {
  const start = Date.now();
  while (true) {
    if (Date.now() - start > timeout) throw new Error("生成超时（超过 10 分钟）");
    const res = await fetch(`${API}/task/${taskId}`);
    if (!res.ok) throw new Error(`查询任务失败 (${res.status})`);
    const task = await res.json();
    if (task.status === "completed") return task;
    if (task.status === "failed") throw new Error(task.error || "生成失败");
    // pending / processing：更新提示并继续等待
    const secs = Math.round((Date.now() - start) / 1000);
    setBusy(true,
      `🖼️ FLUX 正在生成图像... 已等待 ${secs}s\n（首次需加载模型，可能 3-5 分钟）`);
    await new Promise((r) => setTimeout(r, interval));
  }
}

// ---- 调用 /generate（提交任务 → 轮询 → 显示 FLUX 图像）----
async function runGenerate() {
  if (!currentGraph) { toast("请先生成场景图", true); return; }
  switchTab("image");
  setBusy(true, "🚀 正在提交图像生成任务...");
  try {
    const resp = await apiJSON("/generate", {
      scene_graph: graphToInput(currentGraph),
      width: currentGraph.width,
      height: currentGraph.height,
      num_inference_steps: parseInt($("#steps").value, 10) || 32,
      guidance_scale: parseFloat($("#guidance").value) || 3.5,
      save_visualization: true,
    });

    // 情况一：后端已同步返回图像
    if (resp.image_url) {
      showGeneratedImage(resp.image_url);
      toast("✅ 图像生成完成！");
      return;
    }

    // 情况二：FLUX 未加载，仅有布局图
    if (resp.status === "completed" && !resp.image_url) {
      const msg = resp.message || "FLUX 模型未加载，仅返回布局图";
      toast("⚠️ " + msg);
      $("#img-hint").textContent = "⚠️ " + msg;
      return;
    }

    // 情况三：任务在后台生成，轮询等待
    if (!resp.task_id) throw new Error("未返回任务 ID，无法查询进度");
    const task = await pollTask(resp.task_id);
    if (task.image_url) {
      showGeneratedImage(task.image_url);
      toast("✅ 图像生成完成！");
    } else {
      const msg = task.message || "任务完成但未返回图像";
      toast("⚠️ " + msg);
      $("#img-hint").textContent = "⚠️ " + msg;
    }
  } catch (e) {
    console.error("生成失败:", e);
    toast("❌ " + e.message, true);
    $("#img-hint").textContent = "❌ " + e.message;
  } finally {
    setBusy(false);
  }
}

// ---- 显示生成的图像（加时间戳避免缓存）----
function showGeneratedImage(url) {
  const img = $("#layout-img");
  img.src = url + (url.includes("?") ? "&" : "?") + "t=" + Date.now();
  $("#img-hint").textContent = "✅ FLUX 生成的图像";
  switchTab("image");
}

// ---- 统计信息 ----
function updateStats(g) {
  const cats = {};
  g.edges.forEach((e) => { const c = catOf(e.type); cats[c] = (cats[c] || 0) + 1; });
  $("#stat-nodes").textContent = g.elements.length;
  $("#stat-edges").textContent = g.edges.length;
  $("#stat-canvas").textContent = `${g.width}×${g.height}`;
}

// ---- 导出 JSON ----
function exportJSON() {
  if (!currentGraph) { toast("请先生成场景图", true); return; }
  const blob = new Blob([JSON.stringify(graphToInput(currentGraph), null, 2)],
    { type: "application/json" });
  const a = el("a", { href: URL.createObjectURL(blob), download: "scene_graph.json" });
  document.body.append(a); a.click(); a.remove();
}

// ---- 忙碌状态 ----
function setBusy(busy, msg) {
  $("#run-btn").disabled = busy;
  $("#gen-btn").disabled = busy;
  const ov = $("#overlay");
  if (busy) { $("#overlay-msg").textContent = msg || "处理中..."; ov.classList.add("show"); }
  else ov.classList.remove("show");
}

// ---- Tab 切换 ----
function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      $("#panel-" + tab.dataset.tab).classList.add("active");
    });
  });
}

// ---- 健康检查 ----
async function checkHealth() {
  try {
    const res = await fetch(API + "/health");
    const h = await res.json();
    const dot = $("#health-dot");
    dot.className = "health-dot ok";
    $("#health-text").textContent =
      `服务正常 · GPU ${h.gpu_available ? "可用" : "不可用"}`;
  } catch {
    $("#health-dot").className = "health-dot bad";
    $("#health-text").textContent = "服务未连接";
  }
}

// ---- 示例提示词 ----
const EXAMPLES = [
  "一位服务员在咖啡馆的桌前为两位顾客上菜，一个孩子望向窗外",
  "a red car parked next to a blue bicycle under a large tree",
  "a woman reading a book on a bench while a dog sits beside her",
  "两只猫在窗台上，阳光透过玻璃洒进房间",
];
function fillExample() {
  const cur = $("#prompt").value.trim();
  let next = EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)];
  while (next === cur) next = EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)];
  $("#prompt").value = next;
}

// ---- 初始化 ----
function init() {
  initTabs();
  checkHealth();
  $("#run-btn").addEventListener("click", runPredict);
  $("#gen-btn").addEventListener("click", runGenerate);
  $("#example-btn").addEventListener("click", fillExample);
  $("#export-btn").addEventListener("click", exportJSON);
  $("#viz-type").addEventListener("change", () => {
    if (currentGraph) loadServerVisualization(currentGraph);
  });
  $("#prompt").addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runPredict();
  });
}

document.addEventListener("DOMContentLoaded", init);
