import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Download, Hammer, ThumbsDown, ThumbsUp, Upload } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AnimBadge, BackdropPicker, CheckList, CopyButton, Empty, backdropClass } from "@/components/shared";
import { GateTrack } from "@/components/GateTrack";
import { useAct, useGen } from "@/hooks";
import { api, out, type Generation, type Sticker, type VideoSheet } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUI } from "@/store";
import { GenPicker } from "./Generate";

const STATUS: Record<VideoSheet["status"], { tone: "neutral" | "pri" | "ok" | "bad" | "warn"; text: string }> = {
  BUILT: { tone: "pri", text: "built, waiting for your G3 decision" },
  APPROVED: { tone: "ok", text: "approved: send it to your video tool" },
  REJECTED: { tone: "warn", text: "rejected" },
  VIDEO_RETURNED: { tone: "pri", text: "video attached, slicing" },
  VIDEO_BLOCKED: { tone: "bad", text: "video blocked by Python" },
  SLICED: { tone: "ok", text: "video sliced" },
};

/** The video sheet with its slot numbers: filled slots carry the approved S#, blank slots are the rejected ones. */
function SheetPreview({ g, v }: { g: Generation; v: VideoSheet }) {
  const lay = useQuery({ queryKey: ["layout", g.generation_id, v.id], queryFn: () => api.layout(out(g.generation_id, v.layout)) });
  const [cw, ch] = lay.data?.canvas ?? [2048, 2048];
  return (
    <div className="relative overflow-hidden rounded-xl bg-[#00ff00]">
      <img src={out(g.generation_id, v.file)} alt={`Video sheet ${v.id}`} className="block w-full" />
      {lay.data && (
        <svg viewBox={`0 0 ${cw} ${ch}`} className="absolute inset-0 size-full" aria-hidden>
          {lay.data.slots.map((s) => {
            const [x, y, w, h] = s.rect;
            return (
              <g key={s.slot}>
                <rect x={x} y={y} width={w} height={h} fill={s.sticker ? "none" : "#0f172a"} fillOpacity={0.35} stroke="#0f172a" strokeOpacity={0.55} strokeWidth={cw / 400} strokeDasharray={`${cw / 60} ${cw / 100}`} />
                <text x={x + cw / 70} y={y + cw / 22} fontSize={cw / 24} fontWeight="700" fill="#fff" stroke="#0f172a" strokeWidth={cw / 300} paintOrder="stroke">
                  {s.sticker ?? `slot ${s.slot}: blank`}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}

function SlotRow({ g, s, canAnim }: { g: Generation; s: Sticker; canAnim: boolean }) {
  const decide = useAct((d: "APPROVE" | "REJECT") => api.review(g.number, "anim", d, s.index));
  const backdrop = useUI((x) => x.backdrop);
  const inside = s.anim_report?.find((c) => !c.ok && (c.name === "inside_slot" || c.name === "cross_slot"));
  const d = inside?.data as { frame?: number; over_px?: number; px?: number } | undefined;
  return (
    <li className={cn("grid grid-cols-[72px_1fr_auto] items-center gap-3 rounded-xl border bg-sf p-2.5", s.anim_status === "FAILED" ? "border-bad/40" : "border-bd")}>
      <div className={cn("aspect-square overflow-hidden rounded-lg", backdropClass[backdrop])}>
        {s.webm && s.anim_status === "READY" ? (
          <video src={out(g.generation_id, s.webm)} autoPlay loop muted playsInline className="size-full object-contain" />
        ) : s.png ? (
          <img src={out(g.generation_id, s.png)} alt="" className="size-full object-contain" />
        ) : null}
      </div>
      <div className="min-w-0">
        <p className="font-mono text-[12.5px] font-semibold">
          S{s.index} {s.key}
        </p>
        <div className="mt-0.5 flex flex-wrap items-center gap-1">
          <AnimBadge s={s} />
          {(s.anim_metrics.warnings ?? []).map((w) => (
            <Badge key={w} tone="warn">
              {w}
            </Badge>
          ))}
        </div>
        {inside && (
          <p className="mt-1 text-xs text-bad">
            {inside.name}
            {d?.frame != null ? `: frame ${d.frame}, ${d.over_px} px over the slot edge` : d?.px ? `: ${d.px} px of foreground in the gutter` : ""}
          </p>
        )}
        {s.anim_status === "FAILED" && !inside && <p className="mt-1 text-xs text-bad">{s.anim_reason}</p>}
        {s.anim_metrics.subject_px_in_video !== undefined && <p className="mt-0.5 text-[11px] text-mut">subject {String(s.anim_metrics.subject_px_in_video)} px in the video</p>}
      </div>
      <div className="flex gap-1.5">
        {canAnim && s.anim_status === "READY" ? (
          <>
            <Button size="sm" variant={s.review.anim === "APPROVED" ? "ok" : "soft"} onClick={() => decide.mutate(["APPROVE"])} disabled={decide.isPending}>
              <ThumbsUp />
              Approve
            </Button>
            <Button size="sm" variant="bad" onClick={() => decide.mutate(["REJECT"])} disabled={decide.isPending}>
              <ThumbsDown />
              Reject
            </Button>
          </>
        ) : s.anim_status === "FAILED" ? (
          <span className="text-xs text-mut">Python's block is final</span>
        ) : null}
      </div>
    </li>
  );
}

function SheetPanel({ g, v }: { g: Generation; v: VideoSheet }) {
  const file = useRef<HTMLInputElement>(null);
  const go = useUI((x) => x.go);
  const sheetDecision = useAct((d: "APPROVE" | "REJECT") => api.review(g.number, "video_sheet", d, v.id));
  const upload = useAct((f: File) => api.uploadVideo(g.number, v.id, f), "Video attached to " + v.id + ". Python is slicing it.");
  const animAll = useAct(() => api.review(g.number, "anim", "APPROVE", "ready"));
  const st = STATUS[v.status];
  const slots = g.stickers.filter((s) => v.slots.includes(s.index));
  const canDecide = ["BUILT", "APPROVED", "REJECTED"].includes(v.status);
  const canUpload = ["APPROVED", "VIDEO_BLOCKED"].includes(v.status);
  const sliced = v.status === "SLICED";
  const canAnim = sliced && g.reviews.pack?.decision !== "APPROVE";
  const videoUrl = out(g.generation_id, v.video);
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <section aria-label={`Sheet ${v.id}`} className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-[17px] font-bold tracking-tight">Video sheet {v.id}</h2>
          <Badge tone={st.tone}>{st.text}</Badge>
          <span className="text-xs text-mut">
            {v.slots.length} of {g.stickers.length} slots filled
          </span>
        </div>
        <SheetPreview g={g} v={v} />
        <p className="text-xs text-mut">Flat key colour, no outline (it is added once, after the video), rejected stickers left blank. Slot n always holds S n.</p>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="soft" asChild>
            <a href={out(g.generation_id, v.file)} download={`${g.generation_id}-${v.id}-sheet.png`}>
              <Download />
              Download sheet
            </a>
          </Button>
          <CopyButton text={v.video_prompt || g.video_prompt} label="Copy video prompt" />
          {canDecide && (
            <>
              <Button variant={v.status === "APPROVED" ? "ok" : "pri"} onClick={() => sheetDecision.mutate(["APPROVE"])} disabled={sheetDecision.isPending || !!v.blocked}>
                <Check />
                {v.status === "APPROVED" ? "Approved" : "Approve and send to video"}
              </Button>
              <Button variant="bad" onClick={() => sheetDecision.mutate(["REJECT"])} disabled={sheetDecision.isPending}>
                Reject sheet
              </Button>
            </>
          )}
        </div>
        <div className="rounded-xl border border-bd bg-sf p-2.5">
          <h3 className="mb-1 text-[13px] font-semibold">Sheet checks</h3>
          <CheckList checks={v.verify} passing />
        </div>
      </section>

      <section aria-label="Returned video" className="space-y-3">
        <div>
          <h2 className="text-[17px] font-bold tracking-tight">Returned video</h2>
          <p className="text-[13px] text-mut">Make the video from this sheet in your own tool, then upload it here. It is attached to {v.id}, not matched by filename.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={file}
            type="file"
            accept="video/*,.mp4,.mov,.webm,.mkv"
            className="sr-only"
            aria-label="Returned video file"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload.mutate([f]);
              e.target.value = "";
            }}
          />
          <Button variant="pri" disabled={!canUpload || upload.isPending || g.busy} onClick={() => file.current?.click()} title={canUpload ? "" : "Approve the video sheet (G3) first"}>
            <Upload />
            {v.status === "VIDEO_BLOCKED" ? "Upload a corrected video" : "Upload returned video"}
          </Button>
          {g.busy && <Badge tone="pri">Python is working…</Badge>}
        </div>
        {v.video && <video src={videoUrl} controls muted loop className="max-h-64 rounded-xl bg-black" />}
        {v.video_info && (
          <p className="text-xs text-mut">
            {v.video_info.codec} {v.video_info.width}×{v.video_info.height}, {v.video_info.fps} fps, {v.video_info.duration.toFixed(1)} s
          </p>
        )}
        {v.status === "VIDEO_BLOCKED" && (
          <p className="rounded-xl bg-bad-l px-3 py-2 text-[13px] text-bad">
            Python blocked this video ({v.block}). It is not the video of this sheet, so nothing was sliced. Upload a corrected video to {v.id}.
          </p>
        )}
        {v.video_flags?.includes("blank_slots_stay_empty") && (
          <p className="rounded-xl bg-run-l px-3 py-2 text-[13px] text-run">The model added a character to a slot that was blank. The approved slots were still sliced.</p>
        )}
        {(v.video_checks?.length ?? 0) > 0 && (
          <div className="rounded-xl border border-bd bg-sf p-2.5">
            <h3 className="mb-1 text-[13px] font-semibold">Video checks</h3>
            <CheckList checks={v.video_checks ?? []} passing />
          </div>
        )}
        {sliced && (
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-[15px] font-bold">Animations (G4)</h3>
              <BackdropPicker />
              {canAnim && g.gate.active === "anim" && (
                <Button size="sm" variant="pri" onClick={() => animAll.mutate([])} disabled={animAll.isPending}>
                  <Check />
                  Approve all READY
                </Button>
              )}
              {g.gate.active === "pack" && (
                <Button size="sm" variant="pri" onClick={() => go("generate", g.number)}>
                  Go to the final pack
                </Button>
              )}
            </div>
            <ul className="space-y-2">
              {slots.map((s) => (
                <SlotRow key={s.index} g={g} s={s} canAnim={canAnim} />
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}

export default function VideoSheetScreen({ id }: { id: number | null }) {
  const q = useGen(id);
  const go = useUI((s) => s.go);
  const build = useAct(() => api.buildSheet(id as number), (r) => "Built " + r.sheet + " from the approved stills.");
  if (id === null) return <Empty title="No generation yet">Run a task from the Inbox first.</Empty>;
  if (q.isError) return <p className="text-bad">{(q.error as Error).message}</p>;
  const g = q.data;
  if (!g) return <p className="text-mut">Loading…</p>;
  const active = [...g.video_sheets].reverse().find((v) => v.status !== "REJECTED") ?? g.video_sheets[g.video_sheets.length - 1];
  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center gap-4">
        <h1 className="text-2xl font-bold tracking-tight">
          {g.generation_id} <span className="font-medium text-mut">video sheet</span>
        </h1>
        <div className="ml-auto xl:hidden">
          <GenPicker id={id} />
        </div>
      </header>
      <GateTrack g={g} />
      <div className="flex flex-wrap items-center gap-2 rounded-2xl bg-fill/70 px-4 py-2.5">
        <p className="mr-auto text-[13px] font-medium" aria-live="polite">
          {g.gate.message}
        </p>
        <Button variant={g.gate.active === "video_sheet_build" ? "pri" : "soft"} disabled={build.isPending || g.busy || g.gate.active !== "video_sheet_build"} onClick={() => build.mutate([])}>
          <Hammer />
          Build video sheet
        </Button>
        <Button variant="ghost" onClick={() => go("generate", g.number)}>
          Back to the stickers
        </Button>
      </div>
      {g.video_sheets.length > 1 && (
        <p className="text-xs text-mut">
          Earlier sheets: {g.video_sheets.slice(0, -1).map((v) => `${v.id} (${v.status.toLowerCase()})`).join(", ")}
        </p>
      )}
      {active ? (
        <SheetPanel g={g} v={active} />
      ) : (
        <Empty title="No video sheet yet">Approve the stills you want to animate (G2), then build the video sheet. Rejected stickers are left blank on it.</Empty>
      )}
    </div>
  );
}
