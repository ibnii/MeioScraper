import { loadNovel } from "./novel.js?v=20261022";
import { refs } from "./refs.js?v=20261022";

const RECOMMENDATIONS = [
  { title: "Pendeta Kegilaan", slug: "pendeta-kegilaan" },
  { title: "Battle Through the Heavens", slug: "btth" },
  { title: "Swallowed Star", slug: "swallowed-star" },
  { title: "Penguasa Misteri", slug: "lotm" },
  { title: "Dunia Sempurna", slug: "dunia-sempurna" },
  { title: "Teknik Kuno Yang Sangat Kuat", slug: "teknik-kuno-yang-sangat-kuat" },
  { title: "Murid-muridku Semuanya Penjahat", slug: "murid-muridku-semuanya-penjahat" },
  { title: "Xian Ni", slug: "xian-ni" },
];

export function bindRecommendations() {
  const fragment = document.createDocumentFragment();

  for (const item of RECOMMENDATIONS) {
    const row = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "recommendation";
    button.dataset.slug = item.slug;
    button.setAttribute("aria-label", `Muat novel ${item.title}`);

    const title = document.createElement("span");
    title.className = "recommendation__title";
    title.textContent = item.title;

    const slug = document.createElement("span");
    slug.className = "recommendation__slug";
    slug.textContent = item.slug;

    button.append(title, slug);
    row.append(button);
    fragment.append(row);
  }

  refs.recommendationsList.replaceChildren(fragment);

  refs.recommendationsList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-slug]");
    if (!button) return;
    const slug = button.dataset.slug;
    refs.url.value = slug;
    loadNovel(slug);
  });
}
