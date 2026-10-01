import { useState } from "react";
import { Check as CheckIcon, Copy, CircleAlert, CircleCheck, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Check, Sticker } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUI, type Backdrop } from "@/store";

export function CopyButton({ text, label = "Copy", className }: { text: string; label?: string; className?: string }) {
  const [done, setDone] = useState(false);
  return (
    <Button
      size="sm"
      variant="soft"
      className={className}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
        } catch {
          const ta = document.createElement("textarea");
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          ta.remove();
        }
        setDone(true);
        setTimeout(() => setDone(false), 1400);
      }}
    >
      {done ? <CheckIcon /> : <Copy />}
      {done ? "Copied" : label}
    </Button>
  );
}

/** Pretty value for a measured number / limit. */
const fmt = (v: unknown) => (v === null || v === undefined ? "" : typeof v === "number" ? String(Math.round(v * 1000) / 1000) : Array.isArray(v) ? v.join(", ") : String(v));

/** The verifier's rows. BLOCK failures are red and say value against limit; WARN failures are amber and leave the decision to the human. */
export function CheckList({ checks, passing = false }: { checks: Check[]; passing?: boolean }) {
  const rows = passing ? checks : checks.filter((c) => !c.ok);
  if (!rows.length) return <p className="text-xs text-mut">Every check passed.</p>;
  return (
    <ul className="space-y-1">
      {rows.map((c) => {
        const block = !c.ok && (c.severity ?? "BLOCK") === "BLOCK";
        const warn = !c.ok && !block;
        return (
          <li key={c.name} className={cn("rounded-lg px-2.5 py-1.5 text-xs", block && "bg-bad-l text-bad", warn && "bg-run-l text-run", c.ok && "text-mut")}>
            <div className="flex items-center gap-1.5 font-semibold">
              {block ? <ShieldAlert className="size-3.5" /> : warn ? <CircleAlert className="size-3.5" /> : <CircleCheck className="size-3.5 text-ok" />}
              <span className="font-mono">{c.name}</span>
              {!c.ok && <Badge tone={block ? "bad" : "warn"}>{block ? "BLOCK" : "WARN"}</Badge>}
              {c.value !== null && c.value !== undefined && c.limit !== null && c.limit !== undefined && !c.ok && (
                <span className="ml-auto font-normal">
                  {fmt(c.value)} vs limit {fmt(c.limit)}
                </span>
              )}
            </div>
            {c.detail && <div className="pl-5 font-normal opacity-90">{c.detail}</div>}
          </li>
        );
      })}
    </ul>
  );
}

export function StillBadge({ s }: { s: Sticker }) {
  const r = s.review.still;
  if (s.status === "PENDING") return <Badge tone="neutral">waiting</Badge>;
  if (r === "BLOCKED") return <Badge tone="bad">blocked: {s.reason}</Badge>;
  if (r === "APPROVED") return <Badge tone="ok">approved</Badge>;
  if (r === "REJECTED") return <Badge tone="warn">rejected</Badge>;
  return <Badge tone="pri">to review</Badge>;
}

export function AnimBadge({ s }: { s: Sticker }) {
  if (s.anim_status === "NOT_REQUESTED") return null;
  if (s.anim_status === "PROCESSING") return <Badge tone="pri">animating</Badge>;
  if (s.anim_status === "FAILED") return <Badge tone="bad">video blocked: {s.anim_reason}</Badge>;
  const r = s.review.anim;
  return r === "APPROVED" ? <Badge tone="ok">animation approved</Badge> : r === "REJECTED" ? <Badge tone="warn">animation rejected</Badge> : <Badge tone="pri">animation to review</Badge>;
}

const BACKDROPS: [Backdrop, string][] = [
  ["checker", "Checker"],
  ["lightchat", "Light"],
  ["darkchat", "Dark"],
  ["wall", "Wallpaper"],
];
export const backdropClass: Record<Backdrop, string> = { checker: "bg-checker", lightchat: "bg-lightchat", darkchat: "bg-darkchat", wall: "bg-wall" };

/** A white die-cut outline vanishes on light and pops on dark, so every sticker is checked on all four. */
export function BackdropPicker() {
  const { backdrop, setBackdrop } = useUI();
  return (
    <div role="group" aria-label="Preview background" className="inline-flex gap-1.5">
      {BACKDROPS.map(([k, l]) => (
        <button
          key={k}
          aria-pressed={backdrop === k}
          onClick={() => setBackdrop(k)}
          className={cn("rounded-full bg-fill px-3.5 py-1 text-[13px] font-semibold text-[#4b5b6b] hover:bg-[#e5ecf2]", backdrop === k && "bg-pri text-white hover:bg-pri")}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

export function Notice() {
  const { notice, clear } = useUI();
  if (!notice) return null;
  const err = notice.kind === "error";
  return (
    <div
      role={err ? "alert" : "status"}
      className={cn("sticky top-2 z-20 flex items-start gap-2 rounded-xl px-3 py-2 text-[13px] font-medium shadow-sm", err ? "bg-bad-l text-bad" : "bg-ok-l text-ok")}
    >
      {err ? <ShieldAlert className="mt-0.5 size-4 shrink-0" /> : <CircleCheck className="mt-0.5 size-4 shrink-0" />}
      <span className="flex-1">{notice.text}</span>
      <button onClick={clear} className="text-xs underline opacity-80">
        dismiss
      </button>
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-2xl bg-fill/60 px-6 py-12 text-center">
      <p className="font-semibold">{title}</p>
      {children && <div className="mx-auto mt-1 max-w-md text-[13px] text-mut">{children}</div>}
    </div>
  );
}

export const time = (ts: number) => new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
