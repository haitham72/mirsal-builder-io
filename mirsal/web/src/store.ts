import { create } from "zustand";

export type Screen = "inbox" | "generate" | "video" | "history";
export type Backdrop = "checker" | "lightchat" | "darkchat" | "wall";

interface Route {
  screen: Screen;
  id: number | null;
}

export function parseHash(h: string): Route {
  const [, screen, id] = h.replace(/^#/, "").split("/");
  const s = (["inbox", "generate", "video", "history"] as const).find((x) => x === screen) ?? "inbox";
  return { screen: s, id: id && /^\d+$/.test(id) ? Number(id) : null };
}

interface UI extends Route {
  go: (screen: Screen, id?: number | null) => void;
  selected: number | null; // the sticker open in the detail panel
  select: (i: number | null) => void;
  backdrop: Backdrop;
  setBackdrop: (b: Backdrop) => void;
  notice: { kind: "error" | "ok"; text: string } | null;
  say: (kind: "error" | "ok", text: string) => void;
  clear: () => void;
}

export const useUI = create<UI>((set, get) => ({
  ...parseHash(window.location.hash),
  go: (screen, id) => {
    const nid = id === undefined ? get().id : id;
    window.location.hash = `#/${screen}${nid ? `/${nid}` : ""}`;
  },
  selected: null,
  select: (i) => set({ selected: i }),
  backdrop: "checker",
  setBackdrop: (backdrop) => set({ backdrop }),
  notice: null,
  say: (kind, text) => set({ notice: { kind, text } }),
  clear: () => set({ notice: null }),
}));

window.addEventListener("hashchange", () => useUI.setState({ ...parseHash(window.location.hash), selected: null, notice: null }));
