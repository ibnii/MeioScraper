const KEY = "novelin:reader-context";

export function saveReaderContext(novel, chapters) {
  if (!novel?.slug) return;
  try {
    sessionStorage.setItem(
      KEY,
      JSON.stringify({
        slug: novel.slug,
        novel: { slug: novel.slug, title: novel.title, url: novel.url },
        chapters: chapters.map((chapter) => ({
          index: chapter.index,
          title: chapter.title,
          url: chapter.url,
          locked: Boolean(chapter.locked),
          price_label: chapter.price_label ?? null,
        })),
      })
    );
  } catch {
    // Reader can refetch the novel when storage is unavailable.
  }
}

export function readReaderContext(slug) {
  try {
    const data = JSON.parse(sessionStorage.getItem(KEY) || "null");
    if (
      !data ||
      data.slug !== slug ||
      !data.novel ||
      !Array.isArray(data.chapters)
    ) {
      return null;
    }
    return data;
  } catch {
    return null;
  }
}
