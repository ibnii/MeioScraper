import { loadChapter, loadNovel } from "./api.js?v=20261022";
import { readReaderContext } from "./reader-context.js?v=20261022";
import { formatNumber, stripPriceLabel } from "./render.js?v=20261022";

const config = window.NOVELIN_READER || {};
const SIZES = ["0.98rem", "1.08rem", "1.2rem"];
const THEMES = ["paper", "sepia", "night"];
const PREF_THEME = "novelin:reader-theme";
const PREF_SIZE = "novelin:reader-size";

const el = {
  root: document.getElementById("reader"),
  title: document.getElementById("reader-title"),
  novel: document.getElementById("reader-novel"),
  source: document.getElementById("reader-source"),
  close: document.getElementById("reader-close"),
  body: document.getElementById("reader-body"),
  content: document.getElementById("reader-content"),
  loading: document.getElementById("reader-loading"),
  gate: document.getElementById("reader-gate"),
  gateMessage: document.getElementById("reader-gate-message"),
  cookieForm: document.getElementById("reader-cookie-form"),
  cookie: document.getElementById("reader-cookie"),
  error: document.getElementById("reader-error"),
  errorMessage: document.getElementById("reader-error-message"),
  retry: document.getElementById("reader-retry"),
  prev: document.getElementById("reader-prev"),
  next: document.getElementById("reader-next"),
  position: document.getElementById("reader-position"),
  progressFill: document.getElementById("reader-progress-fill"),
  status: document.getElementById("reader-status"),
  sizeButtons: [...document.querySelectorAll("[data-reader-size]")],
  themeButtons: [...document.querySelectorAll("[data-reader-theme]")],
};

const view = {
  novel: null,
  slug: String(config.slug || ""),
  chapters: [],
  byIndex: new Map(),
  index: Number(config.index) || 1,
  cookie: "",
  cache: new Map(),
  size: 1,
  theme: "paper",
  immersive: false,
};

let requestToken = 0;

function readPref(key, fallback) {
  try {
    return window.localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function savePref(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Preferences are a convenience; reading still works without storage.
  }
}

function loadPrefs() {
  const theme = readPref(PREF_THEME, "");
  if (THEMES.includes(theme)) {
    view.theme = theme;
  } else if (document.documentElement.dataset.theme === "dark") {
    view.theme = "night";
  }
  const size = Number(readPref(PREF_SIZE, "1"));
  if (Number.isInteger(size) && size >= 0 && size < SIZES.length) {
    view.size = size;
  }
  applyPrefs();
}

function applyPrefs() {
  el.root.dataset.readerTheme = view.theme;
  el.root.style.setProperty("--reader-font-size", SIZES[view.size]);

  el.themeButtons.forEach((button) => {
    const active = button.dataset.readerTheme === view.theme;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  el.sizeButtons.forEach((button) => {
    const delta = Number(button.dataset.readerSize);
    button.disabled =
      (delta < 0 && view.size === 0) ||
      (delta > 0 && view.size === SIZES.length - 1);
  });
}

function changeSize(delta) {
  const next = Math.min(SIZES.length - 1, Math.max(0, view.size + delta));
  if (next === view.size) return;
  view.size = next;
  applyPrefs();
  savePref(PREF_SIZE, String(next));
}

function setTheme(theme) {
  if (!THEMES.includes(theme)) return;
  view.theme = theme;
  applyPrefs();
  savePref(PREF_THEME, theme);
}

function announce(message) {
  el.status.textContent = "";
  window.requestAnimationFrame(() => {
    el.status.textContent = message;
  });
}

function hasCookie() {
  return view.cookie.trim().length > 0;
}

function setView(name) {
  el.loading.hidden = name !== "loading";
  el.content.hidden = name !== "content";
  el.gate.hidden = name !== "gate";
  el.error.hidden = name !== "error";
}

function updateProgress() {
  const max = el.body.scrollHeight - el.body.clientHeight;
  const percent =
    max > 0 ? Math.min(100, Math.max(0, (el.body.scrollTop / max) * 100)) : 0;
  el.progressFill.style.width = `${percent}%`;
}

function setImmersive(value, notify = true) {
  view.immersive = value;
  el.root.classList.toggle("is-immersive", value);
  if (notify) {
    announce(value ? "Kontrol baca disembunyikan." : "Kontrol baca ditampilkan.");
  }
}

function displayTitle(title, fallback = "") {
  const value = (title || fallback || "").trim();
  const novel = view.novel?.title?.trim();
  if (novel && value.toLowerCase().startsWith(novel.toLowerCase())) {
    const rest = value.slice(novel.length).replace(/^\s*[-–—]\s*/, "").trim();
    if (rest) return rest;
  }
  return value;
}

function chapterHref(index) {
  return `/read/${encodeURIComponent(view.slug)}/${index}`;
}

function updateHeader(chapter) {
  el.novel.textContent = view.novel?.title || "";
  if (!chapter) return;

  el.title.textContent = displayTitle(chapter.title);
  el.source.href = chapter.url;
  el.close.href = `/?url=${encodeURIComponent(
    view.novel?.url || config.novel_url || "/"
  )}`;
  document.title = `${chapter.title} — ${view.novel?.title || "Novelin"}`;
}

function setNav(anchor, chapter) {
  if (chapter) {
    anchor.href = chapterHref(chapter.index);
    anchor.dataset.index = String(chapter.index);
    anchor.title = chapter.title;
    anchor.removeAttribute("aria-disabled");
    return;
  }
  anchor.removeAttribute("href");
  anchor.dataset.index = "";
  anchor.title = "";
  anchor.setAttribute("aria-disabled", "true");
}

function updateNav(chapter) {
  if (!chapter) return;
  setNav(el.prev, view.byIndex.get(chapter.index - 1));
  setNav(el.next, view.byIndex.get(chapter.index + 1));
  el.position.textContent = `${formatNumber(chapter.index)} dari ${formatNumber(
    view.chapters.length
  )}`;
}

function gateMessage(chapter) {
  return `Chapter ini terkunci (${stripPriceLabel(
    chapter.price_label,
    "koin"
  )}). Masukkan cookie akun untuk mencoba membukanya.`;
}

function showLoading(chapter) {
  setView("loading");
  updateHeader(chapter);
  updateNav(chapter);
  el.progressFill.style.width = "0%";
}

function showGate(chapter, message) {
  setView("gate");
  updateHeader(chapter);
  updateNav(chapter);
  el.gateMessage.textContent = message || gateMessage(chapter);
}

function showError(chapter, message) {
  setView("error");
  if (chapter) {
    updateHeader(chapter);
    updateNav(chapter);
  } else {
    el.title.textContent = "Chapter tidak tersedia";
  }
  el.errorMessage.textContent = message || "Coba muat ulang chapter ini.";
}

function renderContent(chapter, payload) {
  el.title.textContent = displayTitle(payload.title, chapter.title);
  el.source.href = chapter.url;
  el.content.innerHTML =
    payload.html || '<p class="reader__empty">Konten chapter tidak tersedia.</p>';

  const lead = [...el.content.querySelectorAll("p")].find(
    (paragraph) => paragraph.textContent.trim().length >= 80
  );
  if (lead) lead.classList.add("reader__lead");

  setView("content");
  updateNav(chapter);
  el.body.scrollTop = 0;
  window.requestAnimationFrame(updateProgress);
}

async function openChapter(chapter) {
  const token = ++requestToken;
  view.index = chapter.index;
  showLoading(chapter);

  if (chapter.locked && !hasCookie()) {
    showGate(chapter);
    return;
  }

  const cacheKey = `${chapter.url}:${hasCookie() ? "cookie" : "anon"}`;
  const cached = view.cache.get(cacheKey);
  if (cached) {
    if (cached.locked) showGate(chapter, cached.gate_message);
    else renderContent(chapter, cached);
    return;
  }

  try {
    const payload = await loadChapter(
      chapter.url,
      hasCookie() ? view.cookie : null
    );
    if (token !== requestToken) return;

    view.cache.set(cacheKey, payload);
    if (payload.locked) {
      showGate(chapter, payload.gate_message);
      return;
    }

    renderContent(chapter, payload);
    announce(`${payload.title || chapter.title} terbuka.`);
  } catch (error) {
    if (token !== requestToken) return;
    showError(chapter, error.message || "Chapter gagal dimuat.");
  }
}

async function resolveNovel() {
  const context = readReaderContext(config.slug);
  if (context && context.chapters.some((chapter) => chapter.index === view.index)) {
    return context;
  }
  return loadNovel(config.novel_url);
}

function goTo(index, push = true) {
  const chapter = view.byIndex.get(index);
  if (!chapter) return;
  if (push) history.pushState({ index }, "", chapterHref(index));
  openChapter(chapter);
}

function bindNav(anchor) {
  anchor.addEventListener("click", (event) => {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }
    const index = Number(anchor.dataset.index);
    if (!Number.isInteger(index) || index < 1) {
      event.preventDefault();
      return;
    }
    event.preventDefault();
    goTo(index);
  });
}

function bind() {
  bindNav(el.prev);
  bindNav(el.next);

  el.sizeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      changeSize(Number(button.dataset.readerSize));
    });
  });

  el.themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setTheme(button.dataset.readerTheme);
    });
  });

  el.retry.addEventListener("click", () => {
    const chapter = view.byIndex.get(view.index);
    if (!chapter) return;
    view.cache.delete(
      `${chapter.url}:${hasCookie() ? "cookie" : "anon"}`
    );
    openChapter(chapter);
  });

  el.cookieForm.addEventListener("submit", (event) => {
    event.preventDefault();
    view.cookie = el.cookie.value.trim();
    view.cache.clear();
    const chapter = view.byIndex.get(view.index);
    if (chapter) openChapter(chapter);
  });

  el.body.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  el.body.addEventListener("click", (event) => {
    if (
      event.target.closest(
        "a, button, input, select, textarea, label, .reader__gate, .reader__error, .reader__loading"
      )
    ) {
      return;
    }
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) return;
    setImmersive(!view.immersive);
  });

  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (event.target.closest("input, select, textarea")) return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      if (el.prev.hasAttribute("href")) el.prev.click();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      if (el.next.hasAttribute("href")) el.next.click();
    } else if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      changeSize(1);
    } else if (event.key === "-") {
      event.preventDefault();
      changeSize(-1);
    } else if (event.key.toLowerCase() === "f") {
      event.preventDefault();
      setImmersive(!view.immersive);
    } else if (event.key === "Escape") {
      event.preventDefault();
      el.close.click();
    }
  });

  window.addEventListener("popstate", () => {
    const match = window.location.pathname.match(/^\/read\/[^/]+\/(\d+)\/?$/);
    if (match) goTo(Number(match[1]), false);
  });
}

async function boot() {
  loadPrefs();
  bind();

  try {
    const data = await resolveNovel();
    view.novel = data.novel;
    view.slug = data.novel.slug || config.slug;
    view.chapters = data.chapters;
    view.byIndex = new Map(
      data.chapters.map((chapter) => [chapter.index, chapter])
    );
    updateHeader(null);

    const chapter = view.byIndex.get(view.index);
    if (!chapter) {
      showError(null, `Chapter ${view.index} tidak ditemukan di novel ini.`);
      return;
    }
    await openChapter(chapter);
  } catch (error) {
    showError(null, error.message || "Gagal memuat novel.");
  }
}

boot();
