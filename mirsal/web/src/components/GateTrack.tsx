import { Check, X } from "lucide-react";
import type { Generation } from "@/lib/api";
import { cn } from "@/lib/utils";

type State = "done" | "active" | "todo" | "stop";
interface Gate {
  id: string;
  label: string;
  state: State;
  note: string;
}

const ACTIVE_AT: Record<string, number> = { plan: 0, still: 1, video_sheet_build: 2, video_sheet: 2, video_upload: 2, anim: 3, pack: 4 };

/** The five gates of the golden path with where this generation stands: the one thing the whole page is built around. */
export function gateStates(g: Generation): Gate[] {
  const S = g.stickers;
  const count = (f: (s: Generation["stickers"][number]) => boolean) => S.filter(f).length;
  const sheet = [...g.video_sheets].reverse().find((v) => v.status !== "REJECTED") ?? null;
  const plan = g.reviews.plan;
  const stills = { ok: count((s) => s.review.still === "APPROVED"), no: count((s) => s.review.still === "REJECTED"), blocked: count((s) => s.review.still === "BLOCKED") };
  const anim = { ok: count((s) => s.review.anim === "APPROVED"), no: count((s) => s.review.anim === "REJECTED"), blocked: count((s) => s.anim_status === "FAILED") };
  const at = ACTIVE_AT[g.gate.active] ?? -1;
  const done = g.gate.active === "done";
  const gates: Gate[] = [
    { id: "G1", label: "Plan", state: plan?.decision === "APPROVE" ? "done" : plan?.decision === "REJECT" ? "stop" : "todo", note: plan ? (plan.decision === "APPROVE" ? "approved" : "rejected") : "to review" },
    {
      id: "G2",
      label: "Stills",
      state: stills.ok + stills.no > 0 && at !== 1 ? "done" : "todo",
      note: `${stills.ok} approved${stills.no ? `, ${stills.no} rejected` : ""}${stills.blocked ? `, ${stills.blocked} blocked` : ""}`,
    },
    {
      id: "G3",
      label: "Video sheet",
      state: sheet && ["APPROVED", "VIDEO_RETURNED", "VIDEO_BLOCKED", "SLICED"].includes(sheet.status) && at !== 2 ? "done" : "todo",
      note: sheet ? `${sheet.id} ${sheet.status.toLowerCase().replace("_", " ")}` : "not built",
    },
    { id: "G4", label: "Animations", state: sheet?.status === "SLICED" && at !== 3 ? "done" : "todo", note: sheet?.status === "SLICED" ? `${anim.ok} approved${anim.blocked ? `, ${anim.blocked} blocked` : ""}${anim.no ? `, ${anim.no} rejected` : ""}` : "waiting for video" },
    { id: "G5", label: "Pack", state: g.reviews.pack?.decision === "APPROVE" ? "done" : "todo", note: g.reviews.pack?.decision === "APPROVE" ? `${g.final.length} stickers final` : "not final" },
  ];
  if (plan?.decision === "REJECT") gates.slice(1).forEach((x) => (x.state = "todo"));
  if (at >= 0) gates[at].state = plan?.decision === "REJECT" ? "stop" : "active";
  if (done) gates.forEach((x) => (x.state = "done"));
  return gates;
}

export function GateTrack({ g }: { g: Generation }) {
  const gates = gateStates(g);
  return (
    <ol aria-label="Gates" className="grid grid-cols-5 gap-0 overflow-hidden rounded-2xl border border-bd bg-sf">
      {gates.map((x, i) => (
        <li
          key={x.id}
          aria-current={x.state === "active" ? "step" : undefined}
          className={cn("relative px-3.5 py-2.5", i > 0 && "border-l border-bd", x.state === "active" && "bg-pri-l", x.state === "stop" && "bg-bad-l")}
        >
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "grid size-6 place-items-center rounded-full text-[11px] font-bold",
                x.state === "done" && "bg-ok text-white",
                x.state === "active" && "bg-pri text-white",
                x.state === "stop" && "bg-bad text-white",
                x.state === "todo" && "bg-fill text-mut",
              )}
            >
              {x.state === "done" ? <Check className="size-3.5" /> : x.state === "stop" ? <X className="size-3.5" /> : x.id.slice(1)}
            </span>
            <span className={cn("text-[13px] font-semibold", x.state === "todo" && "text-mut")}>{x.label}</span>
          </div>
          <p className={cn("mt-1 truncate pl-8 text-xs", x.state === "active" ? "text-pri-d" : "text-mut")}>{x.note}</p>
        </li>
      ))}
    </ol>
  );
}
