export const PAGE_SIZE = 80;

export const state = {
  novel: null,
  stats: { total: 0, free: 0, locked: 0 },
  chapters: [],
  byIndex: new Map(),
  selected: new Set(),
  filter: "all",
  query: "",
  limit: PAGE_SIZE,
  format: "epub",
  progress: new Map(),
  jobId: null,
  jobActive: false,
  jobTotal: 0,
  jobProcessed: 0,
  jobDownloaded: 0,
  eventSource: null,
  loading: false,
};
