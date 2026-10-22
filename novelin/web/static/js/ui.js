import { refs } from "./refs.js";

export function hasCookie() {
  return refs.cookie.value.trim().length > 0;
}

export function isSelectable(chapter) {
  return !chapter.locked || hasCookie();
}

export function clampDelay(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 1;
  return Math.min(10, Math.max(0.25, numeric));
}

export function toast(message, kind = "") {
  const node = document.createElement("div");
  node.className = kind ? `toast toast--${kind}` : "toast";
  node.textContent = message;
  refs.toastRegion.append(node);
  window.setTimeout(() => node.remove(), 4600);
}

export function announce(message) {
  refs.pageStatus.textContent = "";
  window.requestAnimationFrame(() => {
    refs.pageStatus.textContent = message;
  });
}

export function showLookupError(message) {
  if (!message) {
    refs.lookupError.hidden = true;
    refs.lookupError.textContent = "";
    return;
  }
  refs.lookupError.textContent = message;
  refs.lookupError.hidden = false;
}

export function setLookupLoading(active) {
  refs.submit.disabled = active;
  refs.submit.classList.toggle("is-loading", active);
  refs.url.disabled = active;
  refs.submit.querySelector(".btn__label").textContent = active ? "Memuat..." : "Muat novel";
  refs.examples.forEach((button) => {
    button.disabled = active;
  });
}

export function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
