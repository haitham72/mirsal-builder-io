import { useState } from "react";
import { Layers, Search, SquarePen } from "lucide-react";
import { useGenList } from "@/hooks";
import type { GenSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUI } from "@/store";

const STAGE: Record<string, string> = {
  requested: "starting",
  sheet_picked: "keying",
  keyed: "slicing",
  sliced: "to review",
  plan_reviewed: "plan approved",
  stills_reviewed: "stills reviewed",
  video_sheet_built: "video sheet",
  video_sheet_reviewed: "sheet approved",
  video_returned: "video attached",
  video_sliced: "animations",
  anim_reviewed: "animations reviewed",
  pack_final: "pack final",
};

function Avatar({ g }: { g: GenSummary }) {
  return (
    <span className="grid size-12 shrink-0 place-items-center rounded-full border border-bd bg-pri-l text-[17px] font-bold text-pri-d" aria-hidden>
      {(g.subject || "?").slice(0, 1).toUpperCase()}
    </span>
  );
}

/** The list column, where the Mirsal app has its chat list: one row per generation (newest first). */
export function Sidebar({ current }: { current: number | null }) {
  const list = useGenList();
  const { screen, go } = useUI();
  const [q, setQ] = useState("");
  const rows = (list.data?.generations ?? []).filter((g) => `${g.generation_id} ${g.prompt} ${g.subject}`.toLowerCase().includes(q.trim().toLowerCase()));
  return (
    <aside aria-label="Generations" className="hidden min-h-0 flex-col border-r border-bd bg-sf/70 xl:flex">
      <div className="flex items-center justify-between px-5 pb-1 pt-5">
        <h1 className="text-2xl font-bold tracking-tight">Generations</h1>
        <button
          onClick={() => go("inbox", null)}
          aria-label="New task"
          title="New task: prepare a prompt and reserve folders"
          className="grid size-9 place-items-center rounded-xl text-[#526273] hover:bg-fill"
        >
          <SquarePen className="size-5" />
        </button>
      </div>
      <label className="relative mx-5 my-3 block">
        <span className="sr-only">Search generations</span>
        <Search className="pointer-events-none absolute left-3.5 top-3 size-[18px] text-mut2" />
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search generations"
          className="h-10 w-full rounded-xl border border-transparent bg-fill pl-10 pr-3 text-[14px] focus:border-pri focus:bg-white"
        />
      </label>
      <ul className="min-h-0 flex-1 overflow-auto px-2.5 pb-4">
        {rows.map((g) => (
          <li key={g.id}>
            <button
              onClick={() => go(screen === "video" ? "video" : "generate", g.id)}
              aria-current={current === g.id ? "true" : undefined}
              className={cn("flex w-full items-center gap-3.5 rounded-2xl px-3 py-2.5 text-left hover:bg-[#f4f8fb]", current === g.id && "bg-[#EDF3F8]")}
            >
              <Avatar g={g} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[14.5px] font-semibold">
                  {g.generation_id} <span className="font-medium text-mut">{g.subject.replace(/_/g, " ")}</span>
                </span>
                <span className="block truncate text-[13px] text-mut2">{g.error ? `error: ${g.error}` : g.prompt}</span>
              </span>
              <span className="shrink-0 text-[12px] text-mut2">{STAGE[g.stage] ?? g.stage}</span>
            </button>
          </li>
        ))}
        {list.data && rows.length === 0 && (
          <li className="px-4 py-10 text-center text-[13px] text-mut">
            <Layers className="mx-auto mb-2 size-6 text-mut2" />
            {q ? "No generation matches." : "No generations yet. Reserve a task in the Inbox, then run it."}
          </li>
        )}
      </ul>
    </aside>
  );
}
