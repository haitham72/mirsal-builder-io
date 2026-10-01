import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BackdropPicker, CheckList, Empty, backdropClass } from "@/components/shared";
import { api, out, type SearchRow } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUI } from "@/store";
import { HistoryList } from "./Generate";

function Path({ row }: { row: SearchRow }) {
  const q = useQuery({ queryKey: ["gen", row.id], queryFn: () => api.generation(row.id) });
  const go = useUI((s) => s.go);
  const s = q.data?.stickers.find((x) => x.index === row.index);
  if (!s) return <p className="px-3 pb-3 text-xs text-mut">Loading the path…</p>;
  return (
    <div className="mb-3 grid gap-4 rounded-2xl bg-fill/60 px-4 py-3 md:grid-cols-2">
      <div>
        <h4 className="mb-1 text-[13px] font-semibold">Path of {row.generation}/S{row.index}</h4>
        <HistoryList items={s.history} />
      </div>
      <div>
        <h4 className="mb-1 text-[13px] font-semibold">What Python flagged</h4>
        <CheckList checks={[...s.report, ...(s.anim_report ?? [])]} />
        <Button size="sm" variant="soft" className="mt-2" onClick={() => go("generate", row.id)}>
          Open {row.generation}
        </Button>
      </div>
    </div>
  );
}

export default function History() {
  const [q, setQ] = useState("");
  const [d, setD] = useState("");
  const [finalOnly, setFinalOnly] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const backdrop = useUI((s) => s.backdrop);
  useEffect(() => {
    const t = setTimeout(() => setD(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);
  const res = useQuery({ queryKey: ["search", d], queryFn: () => api.search(d), refetchInterval: 4000 });
  const rows = (res.data?.results ?? []).filter((r) => !finalOnly || r.final);
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">History</h1>
        <p className="text-[13px] text-mut">Every sticker with its full path: what Python checked, what you decided, and why. Search by key, tag, name or task.</p>
      </header>
      <div className="flex flex-wrap items-center gap-2">
        <label className="relative">
          <span className="sr-only">Search stickers</span>
          <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-mut2" />
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="teddy, reading, teddy_bear_school"
            className="h-9 w-80 rounded-xl border border-transparent bg-fill pl-9 pr-3 focus:border-pri focus:bg-white"
          />
        </label>
        <label className="flex items-center gap-1.5 text-[13px]">
          <input type="checkbox" checked={finalOnly} onChange={(e) => setFinalOnly(e.target.checked)} className="accent-pri" />
          Final pack only
        </label>
        <BackdropPicker />
        <span className="ml-auto text-xs text-mut">{rows.length} sticker{rows.length === 1 ? "" : "s"}</span>
      </div>
      {res.isError && <p className="text-bad">{(res.error as Error).message}</p>}
      {res.data && rows.length === 0 && <Empty title="Nothing matches">Try a shorter word, a tag such as the pose or the subject, or clear the search.</Empty>}
      <ul>
        {rows.map((r) => {
          const k = `${r.generation}/${r.index}`;
          return (
            <li key={k} className="border-b border-bd/70 last:border-0">
              <button className="grid w-full grid-cols-[56px_1fr_auto] items-center gap-3.5 rounded-2xl px-2 py-3 text-left hover:bg-[#f4f8fb]" aria-expanded={open === k} onClick={() => setOpen(open === k ? null : k)}>
                <div className={cn("aspect-square overflow-hidden rounded-xl border border-bd/70", backdropClass[backdrop])}>{r.png && <img src={out(r.generation, r.png)} alt="" className="size-full object-contain" />}</div>
                <div className="min-w-0">
                  <p className="truncate font-mono text-[12.5px] font-semibold">
                    {r.generation}/S{r.index} {r.key}
                  </p>
                  <p className="truncate text-xs text-mut">{r.tags.join(", ")}</p>
                </div>
                <div className="flex flex-wrap justify-end gap-1">
                  {r.final && <Badge tone="ok">final</Badge>}
                  {r.status === "FAILED" ? <Badge tone="bad">blocked: {r.reason}</Badge> : <Badge tone={r.review.still === "APPROVED" ? "ok" : r.review.still === "REJECTED" ? "warn" : "neutral"}>still {r.review.still.toLowerCase()}</Badge>}
                  {r.anim_status !== "NOT_REQUESTED" && <Badge tone={r.anim_status === "FAILED" ? "bad" : r.review.anim === "APPROVED" ? "ok" : "neutral"}>animation {r.anim_status === "FAILED" ? "blocked" : r.review.anim.toLowerCase()}</Badge>}
                </div>
              </button>
              {open === k && <Path row={r} />}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
