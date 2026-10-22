import { bindChapters } from "./chapters.js";
import { bindJob } from "./job.js";
import { bindNovel, loadNovel } from "./novel.js";
import { bindReader } from "./reader.js";
import { bindRecommendations } from "./recommendations.js";
import { refs } from "./refs.js";
import { initTheme } from "./theme.js";

initTheme();
bindNovel();
bindRecommendations();
bindChapters();
bindJob();
bindReader();

document.addEventListener("keydown", (event) => {
  const active = document.activeElement;
  const typing =
    active &&
    (active.tagName === "INPUT" ||
      active.tagName === "TEXTAREA" ||
      active.isContentEditable);

  if (
    event.key === "/" &&
    !typing &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.altKey
  ) {
    event.preventDefault();
    refs.search.focus();
    return;
  }

  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    refs.downloadBtn.click();
  }
});

const initial = new URLSearchParams(window.location.search).get("url");
if (initial) {
  refs.url.value = initial;
  loadNovel(initial, { scroll: false });
}
