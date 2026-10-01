import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FolderOpen, Play, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CopyButton, Empty } from "@/components/shared";
import { useAct } from "@/hooks";
import { api, type InboxRow, type Task } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUI } from "@/store";

const GRIDS = ["3x3", "2x2", "1x1"] as const;

function useDebounced<T>(v: T, ms = 350) {
  const [d, setD] = useState(v);
  useEffect(() => {
    const t = setTimeout(() => setD(v), ms);
    return () => clearTimeout(t);
  }, [v, ms]);
  return d;
}

function Prompt({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-[13px] font-semibold">{title}</h3>
        <CopyButton text={text} label={`Copy ${title.toLowerCase()}`} />
      </div>
      <textarea readOnly value={text} rows={Math.min(12, text.split("\n").length + 1)} className="w-full resize-y rounded-xl border border-bd bg-fill/60 p-2.5 font-mono text-[12px] leading-[1.5]" />
    </div>
  );
}

function Prepare() {
  const [prompt, setPrompt] = useState("");
  const [grid, setGrid] = useState<(typeof GRIDS)[number]>("3x3");
  const [style, setStyle] = useState("flat_vector");
  const [task, setTask] = useState<Task | null>(null);
  const q = useDebounced(prompt.trim());
  const inbox = useQuery({ queryKey: ["inbox"], queryFn: api.inbox, refetchInterval: 2000 });
  const plan = useQuery({ queryKey: ["plan", q, grid, style], queryFn: () => api.plan(q, grid, style), enabled: q.length > 1, retry: false });
  const reserve = useAct(
    async () => {
      const t = await api.reserve(prompt.trim(), grid, style);
      setTask(t);
      return t;
    },
    (t) => `Reserved ${t.folders.img}. Create that folder and put the sheet in it.`,
  );

  return (
    <section aria-labelledby="prep" className="space-y-4">
      <div>
        <h2 id="prep" className="text-xl font-bold tracking-tight">
          Prepare a task
        </h2>
        <p className="text-[13px] text-mut">Describe the subject, check the prompt, reserve the folder names, then generate in Higgsfield.</p>
      </div>
      {task && (
        <div className="rounded-2xl border border-pri-bd bg-pri-l/60 p-4" aria-live="polite">
          <p className="mb-2 text-[13px] font-semibold text-pri-d">Create these two folders, then name the Higgsfield downloads into them</p>
          {(
            [
              ["Sheet (image)", task.folders.img, task.paths.img],
              ["Video", task.folders.vid, task.paths.vid],
            ] as const
          ).map(([label, name, path]) => (
            <div key={name} className="mb-2 last:mb-0">
              <div className="flex items-center gap-2">
                <span className="w-24 text-xs text-mut">{label}</span>
                <code className="rounded-lg bg-white px-2.5 py-1 text-[15px] font-semibold">{name}</code>
                <CopyButton text={name} label="Copy name" />
                <CopyButton text={path} label="Copy path" />
              </div>
              <div className="ml-26 pl-0.5 font-mono text-[11px] text-mut">{path}</div>
            </div>
          ))}
          <p className="mt-2 text-xs text-mut">
            Task <b>{task.id}</b> is saved (provider {task.provider}, name key <span className="font-mono">{task.name_key}</span>). The app never writes inside the watch
            folders.
          </p>
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
        <label className="block">
          <span className="mb-1 block text-[13px] font-semibold">Subject</span>
          <input
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value);
              setTask(null);
            }}
            placeholder="teddy bear for school"
            className="h-11 w-full rounded-xl border border-transparent bg-fill px-3.5 focus:border-pri focus:bg-white"
          />
        </label>
        <div>
          <span className="mb-1 block text-[13px] font-semibold">Grid</span>
          <div role="radiogroup" aria-label="Grid" className="inline-flex h-11 items-center gap-1.5">
            {GRIDS.map((g) => (
              <button
                key={g}
                role="radio"
                aria-checked={grid === g}
                onClick={() => {
                  setGrid(g);
                  setTask(null);
                }}
                className={cn("h-9 rounded-full bg-fill px-5 text-[14px] font-semibold text-[#4b5b6b]", grid === g && "bg-pri text-white shadow-[0_4px_12px_#3b82f633]")}
              >
                {g.replace("x", "×")}
              </button>
            ))}
          </div>
        </div>
      </div>
      <label className="flex items-center gap-2 text-[13px]">
        <span className="font-semibold">Style</span>
        <select value={style} onChange={(e) => setStyle(e.target.value)} className="h-8 rounded-lg bg-fill px-2">
          {(inbox.data?.styles ?? ["flat_vector"]).map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
      </label>

      {plan.isError && q.length > 1 && <p className="text-[13px] text-bad">{(plan.error as Error).message}</p>}
      {!plan.data && !plan.isError && <Empty title="No prompt yet">Type a subject above. The saved template and its slot JSON fill in here, ready to copy.</Empty>}
      {plan.data && (
        <div className="space-y-3">
          <p className="text-[12.5px] text-mut">
            Template <b className="font-mono text-tx">{plan.data.template_id}</b> v{plan.data.template_version}, {plan.data.stickers.length} cell prompt
            {plan.data.stickers.length > 1 ? "s" : ""}, each with 1 to 5 tags.
          </p>
          <Prompt title="Sheet prompt" text={plan.data.sheet_prompt} />
          <Prompt title="Video prompt" text={plan.data.video_prompt} />
          <details className="rounded-xl border border-bd bg-sf">
            <summary className="cursor-pointer px-3 py-2 text-[13px] font-semibold">Slot JSON and tags</summary>
            <div className="space-y-2 border-t border-bd p-3">
              <ul className="grid gap-1 sm:grid-cols-2">
                {plan.data.stickers.map((s) => (
                  <li key={s.index} className="rounded-lg bg-fill/60 px-2 py-1 text-xs">
                    <span className="font-semibold">
                      {s.index}. {s.emoji} {s.key}
                    </span>
                    <div className="text-mut">{s.tags.slice(1).join(", ") || "no extra tags"}</div>
                  </li>
                ))}
              </ul>
              <pre className="max-h-60 overflow-auto rounded-lg bg-fill/60 p-2 font-mono text-[11px]">{JSON.stringify(plan.data.slots, null, 2)}</pre>
            </div>
          </details>
          <div className="flex items-center gap-2">
            <Button variant="pri" disabled={reserve.isPending || !!task} onClick={() => reserve.mutate([])}>
              <FolderOpen />
              Approve plan and reserve folders
            </Button>
            <span className="text-xs text-mut">Saving is your G1 approval of this plan.</span>
          </div>
        </div>
      )}

    </section>
  );
}

const stateTone = (r: InboxRow) => (r.kind === "invalid" ? "bad" : r.sheets.length ? "ok" : "neutral");

function Row({ r }: { r: InboxRow }) {
  const go = useUI((s) => s.go);
  const run = useAct(
    async () => (r.kind === "task" && r.task ? api.runTask(r.task) : api.runFolder(r.prompt ?? r.subject ?? "", r.variant)),
    (res) => {
      go("generate", res.id);
    },
  );
  const last = r.generations[r.generations.length - 1];
  return (
    <li className="border-b border-bd/70 py-3.5 last:border-0">
      <div className="flex items-center gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-full border border-bd bg-pri-l text-pri-d" aria-hidden>
          {r.kind === "invalid" ? <TriangleAlert className="size-5" /> : <FolderOpen className="size-5" />}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <code className="text-[14px] font-semibold">{r.name}</code>
            <CopyButton text={r.name} label="Copy" />
          </div>
          <div className="mt-1">
            <Badge tone={stateTone(r) as "bad" | "warn" | "ok" | "neutral"}>{r.state}</Badge>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {r.kind !== "invalid" && last && (
            <Button variant="pri" onClick={() => go("generate", Number(last.slice(1)))} title="Open the result that already exists for this folder">
              Open {last}
            </Button>
          )}
          {r.kind !== "invalid" && (
            <Button
              variant={last ? "soft" : "pri"}
              size={last ? "sm" : "md"}
              disabled={!r.can_run || run.isPending}
              onClick={() => run.mutate([])}
              title={last ? "Make another generation from this same folder" : "Key, slice and check this sheet"}
            >
              <Play />
              {last ? "Run again" : "Generate"}
            </Button>
          )}
        </div>
      </div>
      {r.kind === "task" && (
        <p className="mt-1 truncate pl-14 text-xs text-mut">
          {r.prompt} · {r.grid?.[0]}×{r.grid?.[1]} · video folder <span className="font-mono">{r.vid_name}</span>
        </p>
      )}
      {(r.sheets.length > 0 || r.videos.length > 0) && (
        <p className="mt-1 truncate pl-14 font-mono text-[11px] text-mut2">{[...r.sheets, ...r.videos].join("  ")}</p>
      )}
      {r.states.filter((s) => s.includes("ignored")).map((s) => (
        <p key={s} className="mt-1 pl-14 text-xs text-mut2">
          {s}: its own video is used instead.
        </p>
      ))}
      {r.problems.map((p) => (
        <div key={p.nearest} className="mt-2 rounded-lg bg-bad-l p-2 text-xs text-bad">
          <p>This folder {p.what}.</p>
          <p className="text-bad/80">Expected: {p.expected}.</p>
          <p className="mt-1 flex items-center gap-2">
            Rename it to <code className="rounded bg-white px-1.5 py-0.5 font-semibold">{p.nearest}</code>
            <CopyButton text={p.nearest} label="Copy name" />
          </p>
        </div>
      ))}
    </li>
  );
}

function Watch() {
  const q = useQuery({ queryKey: ["inbox"], queryFn: api.inbox, refetchInterval: 2000 });
  return (
    <section aria-labelledby="watch" className="space-y-3">
      <div>
        <h2 id="watch" className="text-xl font-bold tracking-tight">
          Watch folders
        </h2>
        <p className="text-[13px] text-mut">
          Checked every two seconds. Next free number: <b>{q.data ? String(q.data.next_number).padStart(3, "0") : "..."}</b>
        </p>
        <p className="text-[12.5px] text-mut2">One press is one folder: Generate runs that folder, and Open shows what it already made.</p>
        {q.data && (
          <p className="mt-0.5 truncate font-mono text-[11px] text-mut" title={`${q.data.paths.images}\n${q.data.paths.videos}`}>
            {q.data.paths.images}
          </p>
        )}
      </div>
      {q.isError && <p className="text-[13px] text-bad">{(q.error as Error).message}</p>}
      {q.data && q.data.rows.length === 0 && <Empty title="No folders yet">Reserve a task on the left. Its folder shows up here as soon as you create it.</Empty>}
      <ul>{q.data?.rows.map((r) => <Row key={`${r.kind}-${r.name}`} r={r} />)}</ul>
    </section>
  );
}

export default function Inbox() {
  return (
    <div className="grid gap-8 xl:grid-cols-[minmax(0,4fr)_minmax(0,6fr)]">
      <Prepare />
      <Watch />
    </div>
  );
}
