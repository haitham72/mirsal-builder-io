import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Ban, Bot, Check, ChevronRight, RefreshCw, ScanLine, ThumbsDown, ThumbsUp, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AnimBadge, BackdropPicker, CheckList, CopyButton, Empty, StillBadge, backdropClass, time } from "@/components/shared";
import { GateTrack } from "@/components/GateTrack";
import { useAct, useGen, useGenList } from "@/hooks";
import { api, out, type Generation, type HistoryEntry, type Sticker } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUI } from "@/store";

export function GenPicker({ id }: { id: number | null }) {
  const list = useGenList();
  const go = useUI((s) => s.go);
  const screen = useUI((s) => s.screen);
  return (
    <label className="flex items-center gap-2 text-[13px]">
      <span className="font-semibold">Generation</span>
      <select value={id ?? ""} onChange={(e) => go(screen, Number(e.target.value))} className="h-8 max-w-72 rounded-lg bg-fill px-2">
        {list.data?.generations.map((g) => (
          <option key={g.id} value={g.id}>
            {g.generation_id} · {g.prompt}
          </option>
        ))}
      </select>
    </label>
  );
}

/** The measured cut lines on the raw sheet (gutter cuts, not equal thirds). */
function SheetView({ g }: { g: Generation }) {
  const [keyed, setKeyed] = useState(false);
  const grid = g.source.grid;
  const size = g.source.sheet_size;
  const src = keyed ? g.source.keyed : g.source.sheet_copy;
  if (!src || !size) return null;
  const [w, h] = size;
  return (
    <section aria-label="Sheet" className="rounded-2xl border border-bd bg-sf p-3">
      <div className="mb-2 flex items-center gap-2">
        <h3 className="text-[13px] font-semibold">Sheet</h3>
        {grid && <Badge tone={grid.method === "gutter" || grid.method === "single" ? "ok" : "warn"}>cut at {grid.method === "gutter" ? "the gutters" : grid.method}</Badge>}
        <div className="ml-auto inline-flex gap-0.5 rounded-lg bg-fill p-0.5">
          {[
            [false, "Raw"],
            [true, "Keyed"],
          ].map(([k, l]) => (
            <button key={String(l)} aria-pressed={keyed === k} onClick={() => setKeyed(k as boolean)} className={cn("rounded-md px-2 py-0.5 text-xs font-semibold text-mut", keyed === k && "bg-sf text-tx shadow-sm")}>
              {l as string}
            </button>
          ))}
        </div>
      </div>
      <div className={cn("relative overflow-hidden rounded-xl", keyed ? "bg-checker" : "bg-fill")}>
        <img src={out(g.generation_id, src)} alt={keyed ? "Keyed sheet" : "Raw sheet"} className="block w-full" />
        {grid && (
          <svg viewBox={`0 0 ${w} ${h}`} className="absolute inset-0 size-full" aria-hidden>
            {grid.rects.map(([x, y, rw, rh], i) => (
              <g key={i}>
                <rect x={x} y={y} width={rw} height={rh} fill="none" stroke="#2563eb" strokeWidth={Math.max(2, w / 500)} strokeDasharray={`${w / 60} ${w / 100}`} />
                <text x={x + w / 80} y={y + w / 28} fontSize={w / 30} fontWeight="700" fill="#2563eb" stroke="#fff" strokeWidth={w / 400} paintOrder="stroke">
                  {i + 1}
                </text>
              </g>
            ))}
          </svg>
        )}
      </div>
    </section>
  );
}

function Tile({ g, s, canStill, canAnim, showAnim }: { g: Generation; s: Sticker; canStill: boolean; canAnim: boolean; showAnim: boolean }) {
  const { selected, select, backdrop } = useUI();
  const id = g.number;
  const decide = useAct((gate: string, d: "APPROVE" | "REJECT") => api.review(id, gate, d, s.index));
  const blocked = s.status === "FAILED";
  const warns = [...(s.metrics.warnings ?? [])];
  const stillBtns = canStill && s.status === "READY";
  const animBtns = canAnim && s.anim_status === "READY";
  const warnAnim = s.anim_metrics.warnings ?? [];
  const media = showAnim && s.webm && s.anim_status === "READY" ? (
    <video src={out(g.generation_id, s.webm)} autoPlay loop muted playsInline className="size-full object-contain" />
  ) : s.png ? (
    <img src={out(g.generation_id, s.png)} alt={`S${s.index} ${s.key}`} className="size-full object-contain" />
  ) : (
    <div className="grid size-full place-items-center p-3 text-center text-xs font-medium text-bad">{blocked ? s.reason : "waiting"}</div>
  );
  const dim = s.review.still === "REJECTED" || (showAnim && s.review.anim === "REJECTED");
  return (
    <motion.li layout="position" transition={{ duration: 0.18 }} className={cn("overflow-hidden rounded-2xl border bg-sf", selected === s.index ? "border-pri ring-2 ring-pri-l2" : "border-bd")}>
      <button onClick={() => select(selected === s.index ? null : s.index)} className="block w-full text-left" aria-label={`Open S${s.index} ${s.key}`}>
        <div className={cn("relative aspect-square", backdropClass[backdrop], dim && "opacity-45")}>
          {media}
          <span className="absolute left-2 top-2 rounded-md bg-white/90 px-1.5 py-0.5 text-[11px] font-bold shadow-sm">S{s.index}</span>
          <span className="absolute right-2 top-1.5 text-lg" aria-hidden>
            {s.emoji}
          </span>
        </div>
        <div className="space-y-1 px-2.5 pb-1 pt-2">
          <p className="truncate font-mono text-[11.5px] font-semibold" title={s.key}>
            {s.key}
          </p>
          <div className="flex flex-wrap gap-1">
            <StillBadge s={s} />
            <AnimBadge s={s} />
            {[...warns, ...warnAnim].map((w) => (
              <Badge key={w} tone="warn">
                {w}
              </Badge>
            ))}
          </div>
        </div>
      </button>
      <div className="flex gap-1.5 px-2.5 pb-2.5 pt-1.5">
        {stillBtns || animBtns ? (
          <>
            <Button size="sm" variant={(animBtns ? s.review.anim : s.review.still) === "APPROVED" ? "ok" : "soft"} className="flex-1" disabled={decide.isPending} onClick={() => decide.mutate([animBtns ? "anim" : "still", "APPROVE"])}>
              <ThumbsUp />
              Approve
            </Button>
            <Button size="sm" variant="bad" className="flex-1" disabled={decide.isPending} onClick={() => decide.mutate([animBtns ? "anim" : "still", "REJECT"])}>
              <ThumbsDown />
              Reject
            </Button>
          </>
        ) : (
          <p className="flex h-7 items-center gap-1 text-xs text-mut">
            {blocked ? <Ban className="size-3.5 text-bad" /> : null}
            {blocked ? "Python blocked it: final" : s.review.still === "APPROVED" ? "Decision locked or waiting" : ""}
          </p>
        )}
      </div>
    </motion.li>
  );
}

const ACTOR = { python: Bot, human: User, vlm: ScanLine } as const;

export function HistoryList({ items }: { items: HistoryEntry[] }) {
  return (
    <ol className="space-y-1.5">
      {items.map((h, i) => {
        const Icon = ACTOR[h.actor] ?? User;
        const bad = h.decision === "BLOCK" || h.decision === "REJECT";
        return (
          <li key={i} className="flex gap-2 text-xs">
            <span className={cn("mt-0.5 grid size-5 shrink-0 place-items-center rounded-full", h.decision === "BLOCK" ? "bg-bad-l text-bad" : bad ? "bg-run-l text-run" : "bg-ok-l text-ok")}>
              <Icon className="size-3" />
            </span>
            <div className="min-w-0">
              <p>
                <b>{h.stage}</b> {h.decision.toLowerCase()} by {h.actor}
                {h.ref ? ` (${h.ref})` : ""} <span className="text-mut2">{time(h.ts)}</span>
              </p>
              {h.reason && <p className="text-mut">{h.reason}</p>}
              {h.detail?.check && (
                <p className="font-mono text-[11px] text-bad">
                  {h.detail.check}
                  {h.detail.value !== undefined && h.detail.limit !== undefined ? ` ${JSON.stringify(h.detail.value)} vs ${JSON.stringify(h.detail.limit)}` : ""}
                  {h.detail.data && "frame" in h.detail.data && h.detail.data.frame != null ? ` (frame ${String(h.detail.data.frame)}, ${String(h.detail.data.over_px)} px over)` : ""}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function Detail({ g, s }: { g: Generation; s: Sticker }) {
  const select = useUI((x) => x.select);
  const backdrop = useUI((x) => x.backdrop);
  const inbox = useQuery({ queryKey: ["inbox"], queryFn: api.inbox });
  const [subject, setSubject] = useState("");
  const go = useUI((x) => x.go);
  const regen = useAct(() => api.regen(g.number, s.index, subject || undefined), (r) => {
    go("generate", r.id);
  });
  const [all, setAll] = useState(false);
  const m = s.metrics;
  return (
    <motion.aside
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.18 }}
      aria-label={`S${s.index} detail`}
      className="fixed inset-y-0 right-0 z-30 w-[400px] max-w-full space-y-3 overflow-auto border-l border-bd bg-sf p-4 shadow-[-12px_0_32px_-16px_rgba(15,23,42,0.25)]"
    >
      <div className="flex items-start gap-2">
        <div>
          <h3 className="font-mono text-[13px] font-bold">
            S{s.index} {s.key}
          </h3>
          <div className="mt-1 flex flex-wrap gap-1">
            {s.tags.map((t, i) => (
              <Badge key={t} tone={i === 0 ? "pri" : "neutral"}>
                {t}
              </Badge>
            ))}
          </div>
        </div>
        <Button size="icon" variant="ghost" className="ml-auto" aria-label="Close detail" onClick={() => select(null)}>
          ×
        </Button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {[s.png ? <img key="p" src={out(g.generation_id, s.png)} alt="still" className="size-full object-contain" /> : null, s.webm ? <video key="v" src={out(g.generation_id, s.webm)} autoPlay loop muted playsInline className="size-full object-contain" /> : null].map((el, i) => (
          <div key={i} className={cn("aspect-square overflow-hidden rounded-xl", backdropClass[backdrop])}>
            {el ?? <div className="grid size-full place-items-center text-xs text-mut">{i ? "no animation yet" : "no still"}</div>}
          </div>
        ))}
      </div>
      <BackdropPicker />
      <div>
        <h4 className="mb-1 text-[13px] font-semibold">Python checks</h4>
        {s.report.length > 0 && <CheckList checks={s.report} passing={all} />}
        {(s.anim_report?.length ?? 0) > 0 && (
          <>
            <h4 className="mb-1 mt-2 text-[13px] font-semibold">Animation checks</h4>
            <CheckList checks={s.anim_report ?? []} passing={all} />
          </>
        )}
        <button className="mt-1 text-xs text-pri-d underline" onClick={() => setAll(!all)}>
          {all ? "Show only problems" : "Show every check"}
        </button>
      </div>
      <div>
        <h4 className="mb-1 text-[13px] font-semibold">Path</h4>
        <HistoryList items={s.history} />
      </div>
      <details>
        <summary className="cursor-pointer text-[13px] font-semibold">Prompt and measurements</summary>
        <p className="mt-1 text-xs text-mut">{s.prompt}</p>
        <dl className="mt-1 grid grid-cols-2 gap-x-3 text-xs">
          {(["scale", "scale_mode", "threshold", "kb", "chroma_risk", "holes"] as const).map((k) =>
            m[k] !== undefined ? (
              <div key={k} className="flex justify-between">
                <dt className="text-mut">{k}</dt>
                <dd className="font-mono">{String(m[k])}</dd>
              </div>
            ) : null,
          )}
          {s.anim_metrics.subject_px_in_video !== undefined && (
            <div className="flex justify-between">
              <dt className="text-mut">subject px in video</dt>
              <dd className="font-mono">{String(s.anim_metrics.subject_px_in_video)}</dd>
            </div>
          )}
        </dl>
      </details>
      <div className="flex flex-wrap items-center gap-1.5 border-t border-bd pt-2.5">
        <select aria-label="1x1 sheet subject" value={subject} onChange={(e) => setSubject(e.target.value)} className="h-7 rounded-lg bg-fill px-1.5 text-xs">
          <option value="">same subject</option>
          {inbox.data?.subjects.map((x) => (
            <option key={x} value={x}>
              {x}
            </option>
          ))}
        </select>
        <Button size="sm" variant="soft" disabled={regen.isPending} onClick={() => regen.mutate([])} title="Regenerates this one sticker as a 1x1 run through the same engine; it needs a prepared 1x1 sheet.">
          <RefreshCw />
          Regenerate as 1×1
        </Button>
      </div>
    </motion.aside>
  );
}

function PlanTab({ g }: { g: Generation }) {
  const plan = g.reviews.plan;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="space-y-3">
        {[
          ["Sheet prompt", g.sheet_prompt],
          ["Video prompt", g.video_prompt],
        ].map(([t, x]) => (
          <div key={t}>
            <div className="mb-1 flex items-center justify-between">
              <h3 className="text-[13px] font-semibold">{t}</h3>
              <CopyButton text={x} />
            </div>
            <pre className="whitespace-pre-wrap rounded-xl bg-fill/60 p-2.5 font-mono text-[12px]">{x}</pre>
          </div>
        ))}
        <p className="text-xs text-mut">
          Template <b className="font-mono">{g.template_id ?? "hand-written plan"}</b>
          {g.template_version ? ` v${g.template_version}` : ""} · plan from {g.plan_source}
          {plan ? ` · ${plan.decision.toLowerCase()}d by ${plan.by}${plan.note ? `: ${plan.note}` : ""}` : ""}
        </p>
      </div>
      <ul className="space-y-1.5">
        {g.stickers.map((s) => (
          <li key={s.index} className="rounded-xl border border-bd bg-sf px-3 py-2">
            <p className="text-[13px] font-semibold">
              {s.index}. {s.emoji} <span className="font-mono">{s.key}</span>
            </p>
            <p className="text-xs text-mut">{s.prompt}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function FinalTab({ g }: { g: Generation }) {
  const lib = useQuery({ queryKey: ["library"], queryFn: api.library });
  const [pack, setPack] = useState("");
  const [name, setName] = useState("");
  const add = useAct(async () => {
    const pid = pack || (await api.createPack(name || g.task_slug)).id;
    return api.packAdd(g.number, pid);
  }, (r) => `Added ${r.added} animated stickers to the pack.`);
  const approved = g.reviews.pack?.decision === "APPROVE";
  const final = g.stickers.filter((s) => g.final.includes(s.index));
  const { backdrop } = useUI();
  if (!final.length) return <Empty title="No sticker is final yet">A sticker is final when it is approved at both G2 (still) and G4 (animation). Python-blocked stickers never get here.</Empty>;
  return (
    <div className="space-y-3">
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {final.map((s) => (
          <li key={s.index} className="overflow-hidden rounded-2xl border border-bd bg-sf">
            <div className={cn("aspect-square", backdropClass[backdrop])}>{s.webm && <video src={out(g.generation_id, s.webm)} autoPlay loop muted playsInline className="size-full object-contain" />}</div>
            <p className="truncate px-2.5 py-2 font-mono text-[11.5px] font-semibold">
              S{s.index} {s.key}
            </p>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap items-center gap-2">
        <BackdropPicker />
        <select aria-label="Library pack" value={pack} onChange={(e) => setPack(e.target.value)} className="h-9 rounded-xl bg-fill px-2 text-[13px]">
          <option value="">New pack</option>
          {lib.data?.packs.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.stickers.length})
            </option>
          ))}
        </select>
        {!pack && <input aria-label="New pack name" value={name} onChange={(e) => setName(e.target.value)} placeholder={g.task_slug} className="h-9 rounded-xl bg-fill px-3 text-[13px]" />}
        <Button variant="pri" disabled={!approved || add.isPending} onClick={() => add.mutate([])} title={approved ? "" : "Approve the pack (G5) first"}>
          Add to Library pack
        </Button>
      </div>
    </div>
  );
}

function GateActions({ g }: { g: Generation }) {
  const go = useUI((s) => s.go);
  const id = g.number;
  const plan = useAct((d: "APPROVE" | "REJECT") => api.review(id, "plan", d));
  const stills = useAct(() => api.review(id, "still", "APPROVE", "ready"));
  const anim = useAct(() => api.review(id, "anim", "APPROVE", "ready"));
  const pack = useAct((d: "APPROVE" | "REJECT") => api.review(id, "pack", d));
  const build = useAct(() => api.buildSheet(id), () => {
    go("video", id);
  });
  const animate = useAct(() => api.animate(id, "pack"), (r) => (r.noop ? "Already animated." : "Animating with the prepared video."));
  const a = g.gate.active;
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-bd bg-sf px-3.5 py-2.5">
      <p className="mr-auto text-[13px] font-medium" aria-live="polite">
        {g.gate.message}
      </p>
      {a === "plan" && (
        <>
          <Button variant="pri" onClick={() => plan.mutate(["APPROVE"])}>
            <Check />
            Approve plan
          </Button>
          <Button variant="bad" onClick={() => plan.mutate(["REJECT"])}>
            Reject plan
          </Button>
        </>
      )}
      {a === "still" && (
        <Button variant="pri" disabled={stills.isPending} onClick={() => stills.mutate([])}>
          <Check />
          Approve all READY
        </Button>
      )}
      {a === "video_sheet_build" && (
        <Button variant="pri" disabled={build.isPending} onClick={() => build.mutate([])}>
          Build video sheet
          <ChevronRight />
        </Button>
      )}
      {["video_sheet", "video_upload"].includes(a) && (
        <Button variant="pri" onClick={() => go("video", id)}>
          Open video sheet {g.gate.sheet}
          <ChevronRight />
        </Button>
      )}
      {a === "anim" && (
        <Button variant="pri" disabled={anim.isPending} onClick={() => anim.mutate([])}>
          <Check />
          Approve all READY animations
        </Button>
      )}
      {a === "pack" && (
        <>
          <Button variant="ok" onClick={() => pack.mutate(["APPROVE"])}>
            <Check />
            Approve final pack ({g.gate.final?.length ?? 0})
          </Button>
          <Button variant="bad" onClick={() => pack.mutate(["REJECT"])}>
            Reject pack
          </Button>
        </>
      )}
      {g.source.has_video && g.stage !== "requested" && !["wait"].includes(a) && (
        <Button variant="soft" size="sm" disabled={animate.isPending} onClick={() => animate.mutate([])} title="The prepared-video sandbox path: animate from the watch-folder video instead of a video sheet.">
          Animate with the prepared video
        </Button>
      )}
    </div>
  );
}

function Stepper({ g }: { g: Generation }) {
  const done = new Map<string, number>();
  g.events.forEach((e) => {
    if (e.status === "done") done.set(e.stage, (done.get(e.stage) ?? 0) + e.ms);
  });
  const stages = ["requested", "sheet_picked", "keyed", "sliced"];
  return (
    <ol className="flex flex-wrap items-center gap-x-1 gap-y-0.5 text-xs text-mut" aria-label="Stages">
      {stages.map((s, i) => (
        <li key={s} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="size-3 text-mut2" />}
          <span className={cn(done.has(s) ? "font-semibold text-tx" : "")}>{s.replace("_", " ")}</span>
          {done.has(s) && s !== "requested" && <span className="text-mut2">{done.get(s)} ms</span>}
        </li>
      ))}
      {g.events.filter((e) => ["video_returned", "video_sliced"].includes(e.stage) && e.status === "done").map((e, i) => (
        <li key={i} className="flex items-center gap-1">
          <ChevronRight className="size-3 text-mut2" />
          <span className="font-semibold text-tx">{e.stage.replace("_", " ")}</span>
          <span className="text-mut2">{e.ms} ms</span>
        </li>
      ))}
    </ol>
  );
}

export default function Generate({ id }: { id: number | null }) {
  const q = useGen(id);
  const { selected } = useUI();
  const [showAnim, setShowAnim] = useState(false);
  if (id === null) return <Empty title="No generation yet">Run a task from the Inbox: reserve a folder, put the sheet in it, and press Run.</Empty>;
  if (q.isError) return <p className="text-bad">{(q.error as Error).message}</p>;
  const g = q.data;
  if (!g) return <p className="text-mut">Loading…</p>;
  const sheet = [...g.video_sheets].reverse().find((v) => v.status !== "REJECTED");
  const planOk = g.reviews.plan?.decision === "APPROVE";
  const sliced = g.stickers.some((s) => s.status !== "PENDING");
  const canStill = planOk && sliced && !sheet && !g.busy;
  const canAnim = planOk && g.stickers.some((s) => s.anim_status === "READY") && g.reviews.pack?.decision !== "APPROVE" && !g.busy;
  const sel = g.stickers.find((s) => s.index === selected);
  const animView = showAnim || g.gate.active === "anim";
  const hasAnim = g.stickers.some((s) => s.webm);
  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <div>
          <h1 className="text-xl font-bold tracking-tight">
            {g.generation_id} <span className="font-medium text-mut">{g.name_key}</span>
          </h1>
          <p className="text-xs text-mut">
            “{g.prompt}” · {g.grid[0]}×{g.grid[1]} · sheet {g.source.sheet}
            {g.task_id ? ` · task ${g.task_id}` : ""}
            {g.regen_of ? ` · regeneration of ${g.regen_of}` : ""}
          </p>
        </div>
        <div className="ml-auto">
          <GenPicker id={id} />
        </div>
      </header>
      <GateTrack g={g} />
      <GateActions g={g} />
      <Stepper g={g} />
      {g.error && <p className="rounded-xl bg-bad-l px-3 py-2 text-[13px] text-bad">Error: {g.error}</p>}
      {g.verify.sheet?.some((c) => !c.ok) && (
        <div className="rounded-2xl border border-bd bg-sf p-3">
          <h3 className="mb-1 text-[13px] font-semibold">Sheet checks (on arrival)</h3>
          <CheckList checks={g.verify.sheet} />
        </div>
      )}
      <Tabs defaultValue="stills">
        <TabsList>
          <TabsTrigger value="stills">Stickers</TabsTrigger>
          <TabsTrigger value="plan">Plan</TabsTrigger>
          <TabsTrigger value="final">Final pack ({g.final.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="stills" className="mt-3">
          <div className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)]">
            <div className="lg:sticky lg:top-4 lg:self-start">
              <SheetView g={g} />
            </div>
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <BackdropPicker />
                {hasAnim && (
                  <div className="inline-flex gap-0.5 rounded-lg bg-fill p-0.5">
                    {[
                      [false, "Stills"],
                      [true, "Animations"],
                    ].map(([k, l]) => (
                      <button key={String(l)} aria-pressed={animView === k} onClick={() => setShowAnim(k as boolean)} className={cn("rounded-md px-2 py-0.5 text-xs font-semibold text-mut", animView === k && "bg-sf text-tx shadow-sm")}>
                        {l as string}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
                {g.stickers.map((s) => (
                  <Tile key={s.index} g={g} s={s} canStill={canStill} canAnim={canAnim && animView} showAnim={animView} />
                ))}
              </ul>
            </div>
            {sel && <Detail g={g} s={sel} />}
          </div>
        </TabsContent>
        <TabsContent value="plan" className="mt-3">
          <PlanTab g={g} />
        </TabsContent>
        <TabsContent value="final" className="mt-3">
          <FinalTab g={g} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
