const numberFormat = new Intl.NumberFormat("id-ID");
const dateFormat = new Intl.DateTimeFormat("id-ID", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

const STATUS_ICON = {
  done: `<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.4" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="m6.4 10.3 2.3 2.3 4.9-5.2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  skipped: `<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.4" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M6.8 10h6.4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  failed: `<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.4" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="m7.2 7.2 5.6 5.6m0-5.6-5.6 5.6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>`,
};

const LOCK_ICON = `<svg class="badge__lock" viewBox="0 0 12 12" aria-hidden="true"><rect x="2.4" y="5.2" width="7.2" height="5.2" rx="0.8" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M4.2 5.2V4a1.8 1.8 0 0 1 3.6 0v1.2" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>`;

const BOOK_ICON = `<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3.5 4.5h4.1c.8 0 1.5.2 2 .7v10.9c-.5-.5-1.2-.7-2-.7H3.5V4.5Zm13 0h-4.1c-.8 0-1.5.2-2 .7v10.9c.5-.5 1.2-.7 2-.7h4.1V4.5Z" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>`;

export function formatNumber(value) {
  return numberFormat.format(value);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : dateFormat.format(date);
}

function svgElement(markup) {
  const template = document.createElement("template");
  template.innerHTML = markup.trim();
  return template.content.firstElementChild;
}

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

export function stripPriceLabel(value, fallback = "Terkunci") {
  if (!value) return fallback;
  const cleaned = value.replace(/[[\]]/g, "").trim();
  return cleaned || fallback;
}

export function buildNovel(novel, stats, readIndex) {
  const fragment = document.createDocumentFragment();

  const coverWrap = text("div", "novel__cover");
  if (novel.cover_url) {
    const image = document.createElement("img");
    image.className = "cover";
    image.src = novel.cover_url;
    image.alt = `Cover ${novel.title}`;
    image.loading = "lazy";
    image.addEventListener("error", () => {
      image.replaceWith(coverFallback(novel.title));
    });
    coverWrap.append(image);
  } else {
    coverWrap.append(coverFallback(novel.title));
  }

  const body = text("div", "novel__body");
  body.append(text("h2", "novel__title", novel.title));

  if (novel.alternative_title) {
    body.append(text("p", "novel__alt", novel.alternative_title));
  }

  const meta = text("p", "novel__meta");
  const metaItems = [];
  if (novel.author) metaItems.push(["Penulis", novel.author]);
  if (novel.artist) metaItems.push(["Artist", novel.artist]);
  if (novel.status) metaItems.push(["Status", novel.status]);
  if (novel.release) metaItems.push(["Rilis", novel.release]);
  metaItems.push([
    "Chapter",
    `${formatNumber(stats.total)} · ${formatNumber(stats.free)} gratis`,
  ]);
  if (stats.locked) {
    metaItems.push(["Terkunci", formatNumber(stats.locked)]);
  }
  for (const [label, value] of metaItems) {
    const item = text("span");
    item.append(text("strong", null, label), document.createTextNode(` ${value}`));
    meta.append(item);
  }
  body.append(meta);

  if (novel.genres?.length) {
    const genres = text("div", "novel__genres");
    for (const genre of novel.genres) {
      genres.append(text("span", "genre", genre));
    }
    body.append(genres);
  }

  if (novel.synopsis) {
    body.append(buildSynopsis(novel.synopsis));
  }

  const actions = text("div", "novel__actions");
  const read = document.createElement("a");
  read.className = "btn btn--ghost novel__read";
  read.dataset.readFirst = "true";
  read.href = `/read/${encodeURIComponent(novel.slug)}/${readIndex}`;
  read.append(svgElement(BOOK_ICON), document.createTextNode("Mulai baca"));
  actions.append(read);
  body.append(actions);

  const source = document.createElement("a");
  source.className = "novel__source";
  source.href = novel.url;
  source.target = "_blank";
  source.rel = "noreferrer";
  source.textContent = "Lihat di meionovels.com";
  body.append(source);

  fragment.append(coverWrap, body);
  return fragment;
}

function coverFallback(title) {
  const fallback = text("div", "cover cover--fallback", (title || "N").slice(0, 1).toUpperCase());
  fallback.setAttribute("aria-hidden", "true");
  return fallback;
}

function buildSynopsis(synopsis) {
  const wrapper = text("div", "novel__synopsis");
  const paragraphs = synopsis.split(/\n{2,}/).map((part) => part.trim()).filter(Boolean);
  const shortText = paragraphs.slice(0, 2).join("\n\n");
  const needsMore = paragraphs.length > 2 || shortText.length > 480;
  const short = shortText.length > 480 ? `${shortText.slice(0, 480).trimEnd()}…` : shortText;
  const initial = needsMore ? short : shortText;

  const render = (value) => {
    wrapper.replaceChildren();
    for (const part of value.split(/\n{2,}/)) {
      if (part.trim()) wrapper.append(text("p", null, part.trim()));
    }
    if (!needsMore) return;
    const toggle = text("button", "text-btn novel__more", "Baca sinopsis lengkap");
    toggle.type = "button";
    let expanded = false;
    toggle.addEventListener("click", () => {
      expanded = !expanded;
      render(expanded ? synopsis : initial);
    });
    wrapper.append(toggle);
  };

  render(initial);
  return wrapper;
}

export function buildChapterRow(chapter, options) {
  const { selected, selectable, status } = options;
  const row = text("div", "chapter-row");
  row.dataset.index = String(chapter.index);
  row.setAttribute("role", "listitem");
  if (chapter.locked) row.classList.add("is-locked");
  if (selected) row.classList.add("is-selected");
  if (status === "done") row.classList.add("is-done");
  if (status) row.dataset.state = status;

  const check = text("label", "chapter-row__check");
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = selected;
  input.disabled = !selectable;
  input.dataset.index = String(chapter.index);
  input.setAttribute("aria-label", `Pilih ${chapter.title}`);
  if (!selectable) {
    input.title = chapter.locked
      ? "Terkunci. Butuh koin atau cookie akun untuk membuka."
      : "Tidak dapat dipilih.";
  }
  const box = text("span", "box");
  check.append(input, box);

  const index = text(
    "span",
    "chapter-row__index",
    String(chapter.index).padStart(3, "0")
  );

  const main = text("div", "chapter-row__main");
  const title = text("span", "chapter-row__title", chapter.title);
  title.title = chapter.title;
  const date = text("span", "chapter-row__date", formatDate(chapter.release_date));

  let badge;
  if (chapter.locked) {
    badge = text("span", "badge badge--locked");
    badge.append(
      svgElement(LOCK_ICON),
      document.createTextNode(stripPriceLabel(chapter.price_label))
    );
  } else {
    badge = text("span", "badge badge--free", "Gratis");
  }

  main.append(title, date, badge);

  const read = document.createElement("a");
  read.className = "chapter-row__read";
  read.href = `/read/${encodeURIComponent(options.slug)}/${chapter.index}`;
  read.setAttribute("aria-label", `Baca ${chapter.title}`);
  read.title = chapter.locked ? "Baca (chapter mungkin terkunci)" : "Baca chapter";
  read.append(svgElement(BOOK_ICON), document.createTextNode("Baca"));

  const stamp = text("span", "stamp");
  if (status && STATUS_ICON[status]) {
    stamp.append(svgElement(STATUS_ICON[status]));
    stamp.title =
      status === "done" ? "Selesai diunduh" : status === "skipped" ? "Dilewati" : "Gagal";
  }

  row.append(check, index, main, read, stamp);
  return row;
}

export function buildNovelSkeleton() {
  const novel = text("div", "novel-skeleton");
  novel.innerHTML = `
    <div class="skeleton skeleton--cover"></div>
    <div class="skeleton-lines">
      <div class="skeleton skeleton--title"></div>
      <div class="skeleton skeleton--meta"></div>
      <div class="skeleton skeleton--body"></div>
      <div class="skeleton skeleton--body"></div>
      <div class="skeleton skeleton--body-short"></div>
    </div>`;
  return novel;
}

export function buildChapterSkeleton(count = 6) {
  const chapters = text("div", "chapter-skeleton");
  for (let index = 0; index < count; index += 1) {
    const row = text("div", "chapter-skeleton__row");
    row.innerHTML = `
      <div class="skeleton skeleton--box"></div>
      <div class="skeleton skeleton--row-title"></div>
      <div class="skeleton skeleton--row-badge"></div>`;
    chapters.append(row);
  }
  return chapters;
}

export function applyRowState(row, status) {
  if (!row) return;
  if (!status) {
    delete row.dataset.state;
    row.classList.remove("is-done");
  } else {
    row.dataset.state = status;
    row.classList.toggle("is-done", status === "done");
  }

  const stamp = row.querySelector(".stamp");
  if (!stamp) return;
  stamp.replaceChildren();
  stamp.title = "";
  if (status && STATUS_ICON[status]) {
    stamp.append(svgElement(STATUS_ICON[status]));
    stamp.title =
      status === "done" ? "Selesai diunduh" : status === "skipped" ? "Dilewati" : "Gagal";
  }
}
