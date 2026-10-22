import { saveReaderContext } from "./reader-context.js?v=20261022";
import { buildChapterRow, formatNumber } from "./render.js?v=20261022";
import { refs } from "./refs.js?v=20261022";
import { PAGE_SIZE, state } from "./state.js?v=20261022";
import { hasCookie, isSelectable } from "./ui.js?v=20261022";

export function filteredChapters() {
  let list = state.chapters;
  if (state.filter === "free") list = list.filter((chapter) => !chapter.locked);
  if (state.filter === "locked") list = list.filter((chapter) => chapter.locked);

  const query = state.query.trim().toLowerCase();
  if (query) {
    list = list.filter(
      (chapter) =>
        chapter.title.toLowerCase().includes(query) ||
        String(chapter.index).includes(query)
    );
  }
  return list;
}

export function renderChapters() {
  if (!state.novel) return;

  const list = filteredChapters();
  const visible = list.slice(0, state.limit);
  const fragment = document.createDocumentFragment();

  for (const chapter of visible) {
    fragment.append(
      buildChapterRow(chapter, {
        selected: state.selected.has(chapter.index),
        selectable: isSelectable(chapter),
        status: state.progress.get(chapter.index),
        slug: state.novel.slug,
      })
    );
  }

  refs.chapterList.replaceChildren(fragment);
  refs.chapterEmpty.hidden = list.length !== 0;
  refs.loadMore.hidden = list.length <= state.limit;
  const remaining = Math.max(0, list.length - state.limit);
  refs.loadMore.textContent = `Muat ${formatNumber(
    Math.min(PAGE_SIZE, remaining)
  )} chapter lagi`;
  refs.chapterSummary.textContent = `${formatNumber(list.length)} dari ${formatNumber(
    state.chapters.length
  )} chapter`;
  updateSelection();
}

export function updateSelection() {
  const count = state.selected.size;
  const selectableCount = state.chapters.filter(isSelectable).length;

  refs.selectionCount.textContent = `${formatNumber(count)} dipilih`;
  refs.mobileCount.textContent = `${formatNumber(count)} dipilih`;

  if (!state.jobActive) {
    const ratio = selectableCount ? (count / selectableCount) * 100 : 0;
    refs.gaugeFill.style.width = `${Math.min(100, ratio)}%`;
    refs.gaugeMain.textContent = state.novel
      ? `${formatNumber(count)} dipilih`
      : "Belum ada novel";
    refs.gaugeSub.textContent = state.novel
      ? `${formatNumber(selectableCount)} chapter tersedia`
      : "Pilih chapter untuk mulai";
  }

  const busy = state.jobActive;
  refs.downloadBtn.disabled = busy || count === 0;
  refs.downloadBtn.textContent = busy
    ? "Unduhan berjalan"
    : count
      ? `Unduh ${formatNumber(count)} chapter`
      : "Pilih chapter dulu";
  refs.mobileDownload.disabled = busy || count === 0;
  refs.mobileDock.hidden = !state.novel || busy;
  refs.clearSelection.hidden = count === 0;
  refs.clearSelection.disabled = busy;

  const visibleSelectable = filteredChapters().filter(isSelectable);
  const allVisibleSelected =
    visibleSelectable.length > 0 &&
    visibleSelectable.every((chapter) => state.selected.has(chapter.index));
  refs.selectFree.disabled =
    busy || !state.novel || visibleSelectable.length === 0;
  refs.selectFree.textContent =
    visibleSelectable.length === 0
      ? "Tidak ada chapter yang bisa dipilih"
      : allVisibleSelected
        ? "Batalkan pilihan yang tampil"
        : "Pilih semua yang bisa diunduh";

  const hasLockedSelected = [...state.selected].some(
    (index) => state.byIndex.get(index)?.locked
  );
  refs.selectionNote.textContent = hasLockedSelected
    ? "Termasuk chapter terkunci; akan dicoba dengan cookie."
    : "";

  refs.formatButtons.forEach((button) => {
    const active = button.dataset.format === state.format;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
    button.disabled = busy;
  });

  if (refs.mobileFormat) {
    refs.mobileFormat.value = state.format;
    refs.mobileFormat.disabled = busy;
  }

  const coverDisabled = state.format !== "epub";
  refs.includeCover.disabled = busy || coverDisabled;
  refs.includeCover.closest(".switch")?.classList.toggle("is-disabled", coverDisabled);

  if (!state.novel) {
    refs.exportHint.textContent =
      "Chapter berlabel koin tidak akan diunduh tanpa cookie yang sesuai.";
  } else if (busy) {
    refs.exportHint.textContent =
      "Unduhan sedang berjalan. Kamu bisa menghentikannya kapan saja.";
  } else if (!hasCookie() && state.stats.locked) {
    refs.exportHint.textContent =
      "Chapter berlabel koin tidak akan diunduh tanpa cookie yang sesuai.";
  } else if (hasCookie()) {
    refs.exportHint.textContent =
      "Chapter terkunci akan dicoba dengan cookie akunmu; yang tetap terkunci dilewati.";
  } else {
    refs.exportHint.textContent = "Semua chapter dapat diunduh.";
  }
}

export function bindChapters() {
  refs.chapterList.addEventListener("change", (event) => {
    const input = event.target.closest('input[type="checkbox"][data-index]');
    if (!input) return;
    const index = Number(input.dataset.index);
    if (input.checked) state.selected.add(index);
    else state.selected.delete(index);
    input.closest(".chapter-row")?.classList.toggle("is-selected", input.checked);
    updateSelection();
  });

  refs.chapterList.addEventListener("click", (event) => {
    const row = event.target.closest(".chapter-row");
    if (!row || event.target.closest("a, button, input, label")) return;
    const input = row.querySelector('input[type="checkbox"]');
    if (!input || input.disabled) return;
    input.checked = !input.checked;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });

  refs.selectFree.addEventListener("click", () => {
    const list = filteredChapters().filter(isSelectable);
    const allSelected =
      list.length > 0 && list.every((chapter) => state.selected.has(chapter.index));

    for (const chapter of list) {
      if (allSelected) state.selected.delete(chapter.index);
      else state.selected.add(chapter.index);

      const row = refs.chapterList.querySelector(
        `.chapter-row[data-index="${chapter.index}"]`
      );
      if (!row) continue;
      const input = row.querySelector('input[type="checkbox"]');
      if (input) input.checked = !allSelected;
      row.classList.toggle("is-selected", !allSelected);
    }
    updateSelection();
  });

  refs.clearSelection.addEventListener("click", () => {
    state.selected.clear();
    refs.chapterList
      .querySelectorAll('input[type="checkbox"]')
      .forEach((input) => {
        input.checked = false;
      });
    refs.chapterList
      .querySelectorAll(".chapter-row")
      .forEach((row) => row.classList.remove("is-selected"));
    updateSelection();
  });

  refs.chapterList.addEventListener("click", (event) => {
    if (!event.target.closest(".chapter-row__read")) return;
    saveReaderContext(state.novel, state.chapters);
  });

  refs.loadMore.addEventListener("click", () => {
    state.limit += PAGE_SIZE;
    renderChapters();
  });
}
