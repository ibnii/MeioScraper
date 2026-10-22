import { bindChapters } from "./chapters.js?v=20261022";
import { bindJob } from "./job.js?v=20261022";
import { bindNovel, loadNovel } from "./novel.js?v=20261022";
import { bindRecommendations } from "./recommendations.js?v=20261022";
import { refs } from "./refs.js?v=20261022";
import { initTheme } from "./theme.js?v=20261022";

initTheme();
bindNovel();
bindRecommendations();
bindChapters();
bindJob();

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
