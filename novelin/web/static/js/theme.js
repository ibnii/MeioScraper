const KEY = "novelin:theme";

function readStored() {
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function applyTheme(theme, persist) {
  const dark = theme === "dark";
  document.documentElement.dataset.theme = dark ? "dark" : "light";

  const button = document.getElementById("theme-toggle");
  if (button) {
    button.setAttribute("aria-pressed", String(dark));
    button.setAttribute(
      "aria-label",
      dark ? "Aktifkan mode terang" : "Aktifkan mode gelap"
    );
  }

  const label = document.getElementById("theme-toggle-label");
  if (label) label.textContent = dark ? "Terang" : "Gelap";

  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", dark ? "#1C1916" : "#F2EBDD");

  if (persist) {
    try {
      window.localStorage.setItem(KEY, dark ? "dark" : "light");
    } catch {
      // Theme preference is a convenience; the page still works without storage.
    }
  }
}

export function initTheme() {
  const saved = readStored();
  const current = document.documentElement.dataset.theme;
  const initial =
    saved === "dark" || saved === "light"
      ? saved
      : current === "dark"
        ? "dark"
        : "light";

  applyTheme(initial, false);

  document.getElementById("theme-toggle")?.addEventListener("click", () => {
    const next =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next, true);
  });
}
