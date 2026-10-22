import { loadNovel as fetchNovel } from "./api.js";
import { renderChapters, updateSelection } from "./chapters.js";
import { saveReaderContext } from "./reader-context.js";
import {
  buildChapterSkeleton,
  buildNovel,
  buildNovelSkeleton,
  formatNumber,
} from "./render.js";
import { refs } from "./refs.js";
import { PAGE_SIZE, state } from "./state.js";
import {
  announce,
  clampDelay,
  hasCookie,
  prefersReducedMotion,
  setLookupLoading,
  showLookupError,
  toast,
} from "./ui.js";

let searchTimer = 0;
let cookieTimer = 0;

export async function loadNovel(value, options = {}) {
  const scroll = options.scroll !== false;
  if (state.jobActive) {
    toast("Selesaikan atau hentikan unduhan yang sedang berjalan.", "error");
    return;
  }

  const query = String(value || "").trim();
  if (!query) {
    showLookupError("Tempel URL novel atau slug dulu.");
    refs.url.focus();
    return;
  }

  showLookupError("");
  const hadNovel = Boolean(state.novel);
  setLookupLoading(true);
  showSkeleton();

  try {
    const data = await fetchNovel(query);
    state.novel = data.novel;
    state.stats = data.stats;
    state.chapters = data.chapters;
    state.byIndex = new Map(data.chapters.map((chapter) => [chapter.index, chapter]));
    state.selected.clear();
    state.progress.clear();
    state.filter = "all";
    state.query = "";
    state.limit = PAGE_SIZE;
    refs.search.value = "";
    refs.url.value = data.novel.url;
    document.body.classList.add("has-novel");

    refs.novelPanel.hidden = false;
    refs.chaptersPanel.hidden = false;
    renderNovel();
    renderFilters();
    renderChapters();

    history.replaceState(null, "", `?url=${encodeURIComponent(data.novel.url)}`);
    announce(
      `Novel ${data.novel.title} dimuat, ${formatNumber(data.stats.total)} chapter.`
    );

    if (scroll && !hadNovel) {
      const behavior = prefersReducedMotion() ? "auto" : "smooth";
      window.requestAnimationFrame(() => {
        refs.novelPanel.scrollIntoView({ behavior, block: "start" });
      });
    }
  } catch (error) {
    if (hadNovel) {
      renderNovel();
      renderFilters();
      renderChapters();
    } else {
      hidePanels();
    }
    showLookupError(error.message || "Gagal memuat novel.");
    toast(error.message || "Gagal memuat novel.", "error");
  } finally {
    setLookupLoading(false);
  }
}

function showSkeleton() {
  refs.recommendations.hidden = true;
  refs.novelPanel.hidden = false;
  refs.novelPanel.replaceChildren(buildNovelSkeleton());
  refs.chaptersPanel.hidden = false;
  refs.chapterList.replaceChildren(buildChapterSkeleton());
  refs.chapterEmpty.hidden = true;
  refs.loadMore.hidden = true;
  refs.chapterSummary.textContent = "Memuat daftar chapter...";
}

function hidePanels() {
  refs.recommendations.hidden = false;
  refs.novelPanel.hidden = true;
  refs.novelPanel.replaceChildren();
  refs.chaptersPanel.hidden = true;
  refs.chapterList.replaceChildren();
}

export function renderNovel() {
  if (!state.novel) {
    refs.novelPanel.hidden = true;
    refs.novelPanel.replaceChildren();
    return;
  }
  const firstReadable =
    state.chapters.find((chapter) => !chapter.locked) || state.chapters[0];
  refs.novelPanel.replaceChildren(
    buildNovel(state.novel, state.stats, firstReadable?.index)
  );
  refs.novelPanel.hidden = false;
}

export function renderFilters() {
  const counts = {
    all: state.chapters.length,
    free: state.stats.free,
    locked: state.stats.locked,
  };

  for (const button of refs.filters) {
    const key = button.dataset.filter;
    const counter = refs.filterCounts[key];
    if (counter) counter.textContent = formatNumber(counts[key] || 0);
    const active = key === state.filter;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  }
}

export function bindNovel() {
  refs.form.addEventListener("submit", (event) => {
    event.preventDefault();
    loadNovel(refs.url.value);
  });

  refs.examples.forEach((button) => {
    button.addEventListener("click", () => {
      const value = button.dataset.example;
      refs.url.value = value;
      loadNovel(value);
    });
  });

  refs.filters.forEach((button) => {
    button.addEventListener("click", () => {
      if (state.jobActive) return;
      state.filter = button.dataset.filter;
      state.limit = PAGE_SIZE;
      renderFilters();
      renderChapters();
    });
  });

  refs.search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
      state.query = refs.search.value;
      state.limit = PAGE_SIZE;
      renderChapters();
    }, 120);
  });

  refs.search.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    refs.search.value = "";
    state.query = "";
    state.limit = PAGE_SIZE;
    renderChapters();
  });

  refs.cookie.addEventListener("input", () => {
    window.clearTimeout(cookieTimer);
    cookieTimer = window.setTimeout(() => {
      if (!hasCookie()) {
        for (const index of [...state.selected]) {
          if (state.byIndex.get(index)?.locked) state.selected.delete(index);
        }
      }
      renderChapters();
    }, 180);
  });

  refs.formatButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (state.jobActive) return;
      state.format = button.dataset.format;
      updateSelection();
    });
  });

  refs.delay.addEventListener("change", () => {
    refs.delay.value = String(clampDelay(refs.delay.value));
  });

  refs.mobileFormat?.addEventListener("change", () => {
    if (state.jobActive) return;
    state.format = refs.mobileFormat.value;
    updateSelection();
  });

  refs.novelPanel.addEventListener("click", (event) => {
    if (!event.target.closest("[data-read-first]")) return;
    saveReaderContext(state.novel, state.chapters);
  });

  refs.mobileOptions?.addEventListener("click", () => {
    refs.exportPanel?.scrollIntoView({
      behavior: prefersReducedMotion() ? "auto" : "smooth",
      block: "start",
    });
  });
}
