import { loadChapter } from "./api.js";
import { formatNumber, stripPriceLabel } from "./render.js";
import { refs } from "./refs.js";
import { state } from "./state.js";
import { announce, hasCookie, toast } from "./ui.js";

const SIZES = ["0.98rem", "1.08rem", "1.2rem"];
const THEMES = ["paper", "sepia", "night"];
const PREF_THEME = "novelin:reader-theme";
const PREF_SIZE = "novelin:reader-size";

const readerState = {
  index: null,
  cache: new Map(),
  size: 1,
  theme: "paper",
  lastTrigger: null,
  loading: false,
  immersive: false,
};

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
    readerState.theme = theme;
  } else if (document.documentElement.dataset.theme === "dark") {
    readerState.theme = "night";
  } else {
    readerState.theme = "paper";
  }
  const size = Number(readPref(PREF_SIZE, "1"));
  if (Number.isInteger(size) && size >= 0 && size < SIZES.length) {
    readerState.size = size;
  }
  applyPrefs();
}

function applyPrefs() {
  refs.reader.dataset.readerTheme = readerState.theme;
  refs.reader.style.setProperty("--reader-font-size", SIZES[readerState.size]);

  refs.readerThemeButtons.forEach((button) => {
    const active = button.dataset.readerTheme === readerState.theme;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  refs.readerSizeButtons.forEach((button) => {
    const delta = Number(button.dataset.readerSize);
    button.disabled =
      (delta < 0 && readerState.size === 0) ||
      (delta > 0 && readerState.size === SIZES.length - 1);
  });
}

function changeSize(delta) {
  const next = Math.min(SIZES.length - 1, Math.max(0, readerState.size + delta));
  if (next === readerState.size) return;
  readerState.size = next;
  applyPrefs();
  savePref(PREF_SIZE, String(next));
}

function setTheme(theme) {
  if (!THEMES.includes(theme)) return;
  readerState.theme = theme;
  applyPrefs();
  savePref(PREF_THEME, theme);
}

function setView(view) {
  refs.readerLoading.hidden = view !== "loading";
  refs.readerContent.hidden = view !== "content";
  refs.readerGate.hidden = view !== "gate";
  refs.readerError.hidden = view !== "error";
}

function updateProgress() {
  const max = refs.readerBody.scrollHeight - refs.readerBody.clientHeight;
  const percent = max > 0 ? Math.min(100, Math.max(0, (refs.readerBody.scrollTop / max) * 100)) : 0;
  refs.readerProgressFill.style.width = `${percent}%`;
}

function setImmersive(value, notify = true) {
  readerState.immersive = value;
  refs.reader.classList.toggle("is-immersive", value);
  if (notify) {
    announce(
      value ? "Kontrol baca disembunyikan." : "Kontrol baca ditampilkan."
    );
  }
}

function displayTitle(title, fallback = "") {
  const value = (title || fallback || "").trim();
  const novel = state.novel?.title?.trim();
  if (novel && value.toLowerCase().startsWith(novel.toLowerCase())) {
    const rest = value.slice(novel.length).replace(/^\s*[-–—]\s*/, "").trim();
    if (rest) return rest;
  }
  return value;
}

function updateHeader(chapter) {
  refs.readerTitle.textContent = displayTitle(chapter.title);
  refs.readerNovel.textContent = state.novel?.title || "";
  refs.readerSource.href = chapter.url;
}

function updateNav(chapter) {
  const previous = state.byIndex.get(chapter.index - 1);
  const next = state.byIndex.get(chapter.index + 1);

  refs.readerPrev.disabled = !previous;
  refs.readerNext.disabled = !next;
  refs.readerPrev.dataset.index = previous ? String(previous.index) : "";
  refs.readerNext.dataset.index = next ? String(next.index) : "";
  refs.readerPrev.title = previous ? previous.title : "";
  refs.readerNext.title = next ? next.title : "";
  refs.readerPosition.textContent = `${formatNumber(chapter.index)} dari ${formatNumber(
    state.chapters.length
  )}`;
}

function showLoading(chapter) {
  setView("loading");
  updateHeader(chapter);
  updateNav(chapter);
  refs.readerProgressFill.style.width = "0%";
}

function showGate(chapter, message) {
  setView("gate");
  updateHeader(chapter);
  updateNav(chapter);
  refs.readerGateMessage.textContent =
    message ||
    `Chapter ini terkunci (${stripPriceLabel(
      chapter.price_label,
      "koin"
    )}). Masukkan cookie akun untuk mencoba membukanya.`;
}

function showError(chapter, message) {
  setView("error");
  updateHeader(chapter);
  updateNav(chapter);
  refs.readerErrorMessage.textContent = message || "Coba muat ulang chapter ini.";
}

function renderContent(chapter, payload) {
  refs.readerTitle.textContent = displayTitle(payload.title, chapter.title);
  refs.readerNovel.textContent = state.novel?.title || "";
  refs.readerSource.href = chapter.url;
  refs.readerContent.innerHTML =
    payload.html || '<p class="reader__empty">Konten chapter tidak tersedia.</p>';

  const lead = [...refs.readerContent.querySelectorAll("p")].find(
    (paragraph) => paragraph.textContent.trim().length >= 80
  );
  if (lead) lead.classList.add("reader__lead");

  setView("content");
  updateNav(chapter);
  refs.readerBody.scrollTop = 0;
  window.requestAnimationFrame(updateProgress);
}

async function openChapter(chapter) {
  readerState.index = chapter.index;
  showLoading(chapter);

  if (chapter.locked && !hasCookie()) {
    showGate(
      chapter,
      `Chapter ini terkunci (${stripPriceLabel(
        chapter.price_label,
        "koin"
      )}). Masukkan cookie akun untuk mencoba membukanya.`
    );
    return;
  }

  const cacheKey = `${chapter.url}:${hasCookie() ? "cookie" : "anon"}`;
  const cached = readerState.cache.get(cacheKey);
  if (cached) {
    if (cached.locked) showGate(chapter, cached.gate_message);
    else renderContent(chapter, cached);
    return;
  }

  readerState.loading = true;
  try {
    const payload = await loadChapter(
      chapter.url,
      hasCookie() ? refs.cookie.value.trim() : null
    );
    if (readerState.index !== chapter.index) return;

    if (payload.locked) {
      readerState.cache.set(cacheKey, payload);
      showGate(
        chapter,
        payload.gate_message ||
          `Chapter ini masih terkunci untuk akunmu (${stripPriceLabel(
            chapter.price_label,
            "koin"
          )}).`
      );
      return;
    }

    readerState.cache.set(cacheKey, payload);
    renderContent(chapter, payload);
    announce(`${payload.title || chapter.title} terbuka.`);
  } catch (error) {
    if (readerState.index !== chapter.index) return;
    showError(chapter, error.message || "Chapter gagal dimuat.");
  } finally {
    readerState.loading = false;
  }
}

export function openReader(index, trigger) {
  if (!state.novel) return;
  const chapter = state.byIndex.get(index);
  if (!chapter) return;

  if (!refs.reader.open) {
    readerState.lastTrigger = trigger || document.activeElement;
    setImmersive(false, false);
    refs.reader.showModal();
    document.body.classList.add("reader-open");
  }

  readerState.index = index;
  updateHeader(chapter);
  openChapter(chapter);
}

export function closeReader() {
  if (refs.reader.open) refs.reader.close();
}

function openCookieSettings() {
  closeReader();
  refs.advancedOptions.open = true;
  refs.exportPanel.scrollIntoView({ block: "start" });
  window.requestAnimationFrame(() => {
    refs.cookie.focus();
    refs.cookie.scrollIntoView({ block: "center" });
  });
  toast("Tempel cookie akunmu, lalu buka chapter lagi.");
}

export function bindReader() {
  loadPrefs();

  refs.readerClose.addEventListener("click", closeReader);

  refs.reader.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeReader();
  });

  refs.reader.addEventListener("close", () => {
    readerState.index = null;
    setImmersive(false, false);
    document.body.classList.remove("reader-open");
    const trigger = readerState.lastTrigger;
    if (trigger && trigger.isConnected) trigger.focus();
  });

  refs.readerPrev.addEventListener("click", () => {
    const index = Number(refs.readerPrev.dataset.index);
    if (Number.isInteger(index)) openReader(index, refs.readerPrev);
  });

  refs.readerNext.addEventListener("click", () => {
    const index = Number(refs.readerNext.dataset.index);
    if (Number.isInteger(index)) openReader(index, refs.readerNext);
  });

  refs.readerRetry.addEventListener("click", () => {
    const chapter = state.byIndex.get(readerState.index);
    if (!chapter) return;
    readerState.cache.delete(
      `${chapter.url}:${hasCookie() ? "cookie" : "anon"}`
    );
    openChapter(chapter);
  });

  refs.readerCookie.addEventListener("click", openCookieSettings);

  refs.readerSizeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      changeSize(Number(button.dataset.readerSize));
    });
  });

  refs.readerThemeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setTheme(button.dataset.readerTheme);
    });
  });

  refs.readerBody.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  refs.readerBody.addEventListener("click", (event) => {
    if (
      event.target.closest(
        "a, button, input, select, textarea, label, .reader__gate, .reader__error, .reader__loading"
      )
    ) {
      return;
    }
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) return;
    setImmersive(!readerState.immersive);
  });

  refs.reader.addEventListener("keydown", (event) => {
    if (event.target.closest("input, select, textarea")) return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      if (!refs.readerPrev.disabled) refs.readerPrev.click();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      if (!refs.readerNext.disabled) refs.readerNext.click();
    } else if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      changeSize(1);
    } else if (event.key === "-") {
      event.preventDefault();
      changeSize(-1);
    } else if (event.key.toLowerCase() === "f") {
      event.preventDefault();
      setImmersive(!readerState.immersive);
    }
  });

  refs.chapterList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-read-index]");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    openReader(Number(button.dataset.readIndex), button);
  });

  refs.novelPanel.addEventListener("click", (event) => {
    const button = event.target.closest("[data-read-first]");
    if (!button) return;
    const chapter =
      state.chapters.find((item) => !item.locked) || state.chapters[0];
    if (chapter) openReader(chapter.index, button);
  });

  refs.cookie.addEventListener("input", () => {
    readerState.cache.clear();
  });
}
