// Thin typed client over the stdlib server's JSON API. Every control in the app calls one of these.
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function call<T>(method: string, url: string, body?: unknown, raw?: BodyInit): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: raw ? undefined : body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: raw ?? (body !== undefined ? JSON.stringify(body) : undefined),
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) throw new ApiError(res.status, (data as { error?: string } | null)?.error ?? `${res.status} ${res.statusText}`);
  return data as T;
}

export interface Check {
  name: string;
  ok: boolean;
  detail: string;
  severity?: "BLOCK" | "WARN";
  stage?: string;
  value?: unknown;
  limit?: unknown;
  data?: Record<string, unknown>;
}
export interface HistoryEntry {
  ts: number;
  stage: string;
  actor: "python" | "human" | "vlm";
  decision: string;
  reason: string | null;
  ref: string | null;
  detail: { check?: string; value?: unknown; limit?: unknown; note?: string; data?: Record<string, unknown>; warnings?: string[] } | null;
}
export type StillState = "PENDING" | "APPROVED" | "REJECTED" | "BLOCKED";
export interface Sticker {
  index: number;
  key: string;
  tags: string[];
  emoji: string;
  prompt: string;
  name: string;
  status: "PENDING" | "READY" | "FAILED";
  reason: string | null;
  report: Check[];
  metrics: Record<string, unknown> & { warnings?: string[] };
  png: string | null;
  webm: string | null;
  anim_status: "NOT_REQUESTED" | "PROCESSING" | "READY" | "FAILED";
  anim_reason: string | null;
  anim_metrics: Record<string, unknown> & { warnings?: string[] };
  anim_report?: Check[];
  review: { still: StillState; anim: StillState | "NONE" };
  history: HistoryEntry[];
}
export interface VideoSheet {
  id: string;
  slots: number[];
  grid: [number, number];
  file: string;
  layout: string;
  video: string | null;
  video_name?: string;
  status: "BUILT" | "APPROVED" | "REJECTED" | "VIDEO_RETURNED" | "VIDEO_BLOCKED" | "SLICED";
  verify: Check[];
  blocked: string | null;
  block?: string | null;
  video_checks?: Check[];
  video_flags?: string[];
  video_info?: { codec: string; width: number; height: number; fps: number; duration: number };
  video_prompt: string;
}
export interface Stamp {
  decision: "APPROVE" | "REJECT";
  by: string;
  ts: number;
  note: string | null;
  stickers?: number[];
}
export interface GateInfo {
  active: string;
  message: string;
  pending?: number[];
  final?: number[];
  sheet?: string;
  blocked?: string | null;
}
export interface GenEvent {
  ts: number;
  stage: string;
  status: string;
  ms: number;
  detail: Record<string, unknown> | null;
  actor?: string;
  decision?: string;
}
export interface Slots {
  subject_description: string;
  cells: { pos: number; label: string; tags: string[]; emoji: string }[];
}
export interface Generation {
  generation_id: string;
  number: number;
  parent: number | null;
  prompt: string;
  task: string;
  task_slug: string;
  name_key: string;
  task_id: string | null;
  regen_of: string | null;
  grid: [number, number];
  stage: string;
  stages: string[];
  error: string | null;
  busy: boolean;
  plan_source: string;
  sheet_prompt: string;
  video_prompt: string;
  template_id: string | null;
  template_version: number | null;
  slots: Slots | null;
  source: {
    subject: string;
    variant: number;
    n_variants: number;
    sheet: string;
    sheet_copy?: string;
    keyed?: string;
    sheet_size?: [number, number];
    has_video: boolean;
    grid?: { rows: number; cols: number; rects: number[][]; xs: number[]; ys: number[]; method: string };
  };
  reviews: { plan: Stamp | null; video_sheet: Record<string, Stamp>; pack: Stamp | null };
  video_sheets: VideoSheet[];
  verify: { sheet?: Check[] };
  stickers: Sticker[];
  events: GenEvent[];
  gate: GateInfo;
  final: number[];
}
export interface GenSummary {
  id: number;
  generation_id: string;
  prompt: string;
  stage: string;
  subject: string;
  variant: number;
  error: string | null;
}
export interface Plan {
  task: string;
  task_slug: string;
  grid: [number, number];
  template_id: string;
  template_version: number;
  slots: Slots & Record<string, unknown>;
  sheet_prompt: string;
  video_prompt: string;
  stickers: { index: number; key: string; tags: string[]; emoji: string; prompt: string }[];
}
export interface Task {
  id: string;
  number: number;
  provider: string;
  external_task_id: string;
  name_key: string;
  prompt: string;
  folders: { img: string; vid: string };
  paths: { img: string; vid: string };
  plan: Plan;
}
export interface InboxRow {
  kind: "task" | "folder" | "invalid";
  task: string | null;
  name: string;
  vid_name?: string;
  subject: string | null;
  prompt?: string;
  grid?: [number, number];
  variant?: number | null;
  states: string[];
  state: string;
  sheets: string[];
  videos: string[];
  can_run: boolean;
  paths: Record<string, string>;
  generations: string[];
  problems: { what: string; expected: string; nearest: string }[];
}
export interface Inbox {
  next_number: number;
  paths: { images: string; videos: string };
  rows: InboxRow[];
  subjects: string[];
  grids: string[];
  styles: string[];
}
export interface SearchRow {
  generation: string;
  id: number;
  index: number;
  key: string;
  tags: string[];
  name: string;
  task_slug: string;
  status: string;
  reason: string | null;
  review: Sticker["review"];
  anim_status: string;
  png: string | null;
  webm: string | null;
  emoji: string;
  final: boolean;
}
export interface Library {
  packs: { id: string; name: string; stickers: unknown[] }[];
}
export interface Layout {
  canvas: [number, number];
  slots: { slot: number; sticker: string | null; rect: number[]; subject_rect: number[] | null }[];
}

export const api = {
  generations: () => call<{ busy: boolean; health: { vp9: boolean; ffmpeg: string | null }; generations: GenSummary[] }>("GET", "/api/generations"),
  generation: (id: number) => call<Generation>("GET", `/api/generations/${id}`),
  inbox: () => call<Inbox>("GET", "/api/inbox"),
  plan: (prompt: string, grid: string, style_id: string) => call<Plan>("POST", "/api/plan", { prompt, grid, style_id }),
  reserve: (prompt: string, grid: string, style_id: string) => call<Task>("POST", "/api/tasks", { prompt, grid, style_id }),
  runTask: (task: string) => call<{ id: number }>("POST", "/api/generations", { task }),
  runFolder: (prompt: string, variant: number | null | undefined) => call<{ id: number }>("POST", "/api/generations", { prompt, variant }),
  review: (id: number, gate: string, decision: "APPROVE" | "REJECT", index?: number | string, note?: string) =>
    call<{ ok: boolean }>("POST", `/api/generations/${id}/review`, { gate, decision, index, note }),
  buildSheet: (id: number) => call<{ sheet: string }>("POST", `/api/generations/${id}/video_sheet`),
  uploadVideo: (id: number, aid: string, file: File) =>
    call<{ id: number }>("POST", `/api/generations/${id}/video_sheet/${aid}/video?name=${encodeURIComponent(file.name)}`, undefined, file),
  animate: (id: number, scope: "pack" | "slice", index?: number) => call<{ noop?: boolean }>("POST", `/api/generations/${id}/animate`, { scope, index }),
  regen: (id: number, index: number, subject?: string) => call<{ id: number }>("POST", `/api/generations/${id}/regen`, { index, subject }),
  library: () => call<Library>("GET", "/api/library"),
  createPack: (name: string) => call<{ id: string }>("POST", "/api/packs", { name }),
  packAdd: (id: number, pack_id: string) => call<{ added: number }>("POST", `/api/generations/${id}/pack_add`, { pack_id }),
  search: (q: string) => call<{ results: SearchRow[] }>("GET", `/api/search?q=${encodeURIComponent(q)}`),
  layout: (url: string) => call<Layout>("GET", url),
};

export const out = (id: string, rel: string | null | undefined) => (rel ? `/out/${id}/${rel}` : "");
