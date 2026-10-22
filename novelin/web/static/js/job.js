import { cancelJob, startJob, watchJob } from "./api.js?v=20261022";
import { applyRowState, formatNumber } from "./render.js?v=20261022";
import { refs } from "./refs.js?v=20261022";
import { renderChapters, updateSelection } from "./chapters.js?v=20261022";
import { state } from "./state.js?v=20261022";
import { announce, clampDelay, toast } from "./ui.js?v=20261022";

export function bindJob() {
  refs.downloadBtn.addEventListener("click", startDownload);
  refs.mobileDownload.addEventListener("click", startDownload);
  refs.cancelJob.addEventListener("click", cancelDownload);
}

export async function startDownload() {
  if (state.jobActive || !state.novel || state.selected.size === 0) return;

  const chapters = [...state.selected].sort((left, right) => left - right);
  const payload = {
    url: state.novel.url,
    chapters,
    format: state.format,
    include_cover: state.format === "epub" && refs.includeCover.checked,
    delay: clampDelay(refs.delay.value),
    cookie: refs.cookie.value.trim() || null,
  };

  state.progress.clear();
  state.jobTotal = chapters.length;
  state.jobProcessed = 0;
  state.jobDownloaded = 0;
  state.jobId = null;
  resetJobPanel(chapters.length);
  setJobActive(true);
  renderChapters();
  announce("Unduhan dimulai.");

  try {
    const result = await startJob(payload);
    state.jobId = result.job_id;
    refs.cancelJob.disabled = false;
    state.eventSource = watchJob(result.job_id, {
      onEvent: handleJobEvent,
      onError: () => {
        if (!state.jobActive) return;
        refs.jobStatus.textContent = "Koneksi progres terputus. Mencoba lagi...";
      },
    });
  } catch (error) {
    setJobActive(false);
    refs.jobStatus.textContent = "Gagal memulai unduhan.";
    toast(error.message || "Gagal memulai unduhan.", "error");
  }
}

export async function cancelDownload() {
  if (!state.jobId) return;
  refs.cancelJob.disabled = true;
  refs.jobStatus.textContent = "Menghentikan setelah chapter ini...";
  try {
    await cancelJob(state.jobId);
  } catch (error) {
    refs.cancelJob.disabled = false;
    toast(error.message || "Gagal menghentikan unduhan.", "error");
  }
}

function resetJobPanel(total) {
  refs.jobPanel.hidden = false;
  refs.jobStatus.textContent = "Menyiapkan unduhan...";
  refs.jobCount.textContent = `0 / ${formatNumber(total)} chapter`;
  refs.jobProgressFill.style.width = "0%";
  refs.jobProgress.setAttribute("aria-valuenow", "0");
  refs.jobProgress.setAttribute("aria-valuetext", `0 dari ${total} chapter`);
  refs.jobLog.replaceChildren();
  refs.jobDownload.hidden = true;
  refs.jobDownload.removeAttribute("href");
  refs.jobDownload.removeAttribute("download");
  refs.cancelJob.disabled = true;
  refs.cancelJob.hidden = false;
  refs.gaugeFill.style.width = "0%";
  refs.gaugeMain.textContent = `0 dari ${formatNumber(total)}`;
  refs.gaugeSub.textContent = "0 tersimpan";
}

function setJobActive(active) {
  state.jobActive = active;
  refs.url.disabled = active;
  refs.submit.disabled = active;
  refs.examples.forEach((button) => {
    button.disabled = active;
  });
  refs.cookie.disabled = active;
  refs.delay.disabled = active;
  refs.cancelJob.disabled = !active;
  updateSelection();
}

function handleJobEvent(event) {
  if (event.type === "stage") {
    refs.jobStatus.textContent = event.message;
    return;
  }

  if (event.type === "start") {
    state.jobTotal = event.total;
    state.jobProcessed = 0;
    refs.jobStatus.textContent = `Mengunduh ${event.title}`;
    refs.jobCount.textContent = `0 / ${formatNumber(event.total)} chapter`;
    return;
  }

  if (event.type === "chapter") {
    handleChapter(event);
    return;
  }

  if (event.type === "done") {
    handleDone(event);
    return;
  }

  if (event.type === "error") {
    handleError(event);
  }
}

function handleChapter(event) {
  if (["done", "skipped", "failed"].includes(event.status)) {
    state.progress.set(event.index, event.status);
    const row = refs.chapterList.querySelector(
      `.chapter-row[data-index="${event.index}"]`
    );
    applyRowState(row, event.status);
  }

  state.jobTotal = event.total;
  state.jobProcessed = event.processed;
  state.jobDownloaded = event.downloaded;

  const percent = event.total
    ? Math.round((event.processed / event.total) * 100)
    : 0;
  refs.jobProgressFill.style.width = `${percent}%`;
  refs.jobProgress.setAttribute("aria-valuenow", String(percent));
  refs.jobProgress.setAttribute(
    "aria-valuetext",
    `${event.processed} dari ${event.total} chapter`
  );
  refs.jobCount.textContent = `${formatNumber(event.processed)} / ${formatNumber(
    event.total
  )} chapter · ${formatNumber(event.downloaded)} tersimpan`;

  refs.gaugeFill.style.width = `${percent}%`;
  refs.gaugeMain.textContent = `${formatNumber(event.processed)} dari ${formatNumber(
    event.total
  )}`;
  refs.gaugeSub.textContent = `${formatNumber(event.downloaded)} tersimpan`;

  if (event.status === "downloading") {
    refs.jobStatus.textContent = `Mengunduh ${event.title}...`;
  } else {
    addLog(event);
  }
}

function handleDone(event) {
  setJobActive(false);
  state.jobId = null;
  state.eventSource?.close();
  state.eventSource = null;
  refs.cancelJob.disabled = true;
  refs.cancelJob.hidden = true;

  const summary = `${formatNumber(event.downloaded)} tersimpan · ${formatNumber(
    event.skipped
  )} dilewati · ${formatNumber(event.failed)} gagal`;
  const percent = state.jobTotal
    ? Math.min(100, Math.round((state.jobProcessed / state.jobTotal) * 100))
    : 0;
  refs.gaugeFill.style.width = `${percent}%`;

  if (event.downloaded === 0 && !event.cancelled) {
    const message =
      event.message || "Tidak ada chapter yang bisa diunduh.";
    refs.jobStatus.textContent = message;
    refs.jobCount.textContent = summary;
    refs.gaugeMain.textContent = "Tidak ada berkas";
    refs.gaugeSub.textContent = `${formatNumber(event.skipped)} dilewati`;
    toast(message, "error");
    announce(message);
    return;
  }

  refs.jobStatus.textContent = event.cancelled ? "Dihentikan." : "Selesai.";
  refs.jobCount.textContent = summary;
  refs.gaugeMain.textContent = event.cancelled ? "Dihentikan" : "Selesai";
  refs.gaugeSub.textContent = `${formatNumber(event.downloaded)} chapter tersimpan`;

  if (event.file) {
    refs.jobDownload.href = event.file;
    refs.jobDownload.setAttribute("download", event.filename || "");
    refs.jobDownload.textContent = `Simpan ${event.filename || "berkas"}`;
    refs.jobDownload.hidden = false;
  } else {
    refs.jobDownload.hidden = true;
    refs.jobDownload.removeAttribute("href");
    refs.jobDownload.removeAttribute("download");
  }

  if (event.cancelled) {
    toast("Unduhan dihentikan. Chapter yang selesai tetap disimpan.");
    announce("Unduhan dihentikan.");
  } else {
    toast(`Selesai. ${formatNumber(event.downloaded)} chapter tersimpan.`);
    announce(`Unduhan selesai. ${event.downloaded} chapter tersimpan.`);
  }
}

function handleError(event) {
  setJobActive(false);
  state.jobId = null;
  state.eventSource?.close();
  state.eventSource = null;
  refs.cancelJob.disabled = true;
  refs.cancelJob.hidden = true;
  refs.jobStatus.textContent = "Gagal.";
  refs.gaugeMain.textContent = "Gagal";
  refs.gaugeSub.textContent = "Tidak ada berkas";
  addLog({ status: "failed", title: "Unduhan", message: event.message });
  toast(event.message || "Unduhan gagal.", "error");
  announce("Unduhan gagal.");
}

function addLog(event) {
  const marks = { done: "✓", skipped: "–", failed: "×" };
  const item = document.createElement("li");
  const mark = document.createElement("span");
  mark.className = `log-mark log-mark--${event.status}`;
  mark.textContent = marks[event.status] || "·";

  const label = document.createElement("span");
  if (event.status === "skipped") label.textContent = `${event.title} — dilewati`;
  else if (event.status === "failed") {
    label.textContent = `${event.title} — gagal${event.message ? `: ${event.message}` : ""}`;
  } else {
    label.textContent = event.title;
  }

  item.append(mark, label);
  refs.jobLog.prepend(item);
  while (refs.jobLog.children.length > 8) {
    refs.jobLog.lastElementChild.remove();
  }
}
