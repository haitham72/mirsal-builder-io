import { useEffect, useRef } from "react";
import { History as HistoryIcon, Inbox as InboxIcon, Layers, Library, Scissors } from "lucide-react";
import { Notice } from "@/components/shared";
import { useGenList } from "@/hooks";
import { cn } from "@/lib/utils";
import { useUI, type Screen } from "@/store";
import Generate from "@/screens/Generate";
import History from "@/screens/History";
import Inbox from "@/screens/Inbox";
import VideoSheetScreen from "@/screens/VideoSheet";

const NAV: { id: Screen; label: string; icon: typeof InboxIcon }[] = [
  { id: "inbox", label: "Inbox", icon: InboxIcon },
  { id: "generate", label: "Generate", icon: Layers },
  { id: "video", label: "Video sheet", icon: Scissors },
  { id: "history", label: "History", icon: HistoryIcon },
];

export default function App() {
  const { screen, id, go } = useUI();
  const list = useGenList();
  // Generate and Video work on one generation: the one in the URL, else the newest.
  const current = id ?? list.data?.generations[0]?.id ?? null;
  const health = list.data?.health;
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    main.current?.scrollTo(0, 0);
  }, [screen, id]);

  return (
    <div className="grid h-full grid-cols-[88px_1fr]">
      <nav aria-label="Main" className="flex flex-col items-center gap-1 border-r border-bd bg-sf/80 py-3.5">
        <div className="mb-3 grid size-10 place-items-center rounded-xl bg-pri text-lg font-extrabold text-white" aria-hidden>
          M
        </div>
        {NAV.map(({ id: n, label, icon: Icon }) => (
          <button
            key={n}
            aria-current={screen === n ? "page" : undefined}
            onClick={() => go(n, n === "generate" || n === "video" ? current : null)}
            className={cn(
              "flex w-[72px] flex-col items-center gap-1 rounded-2xl py-2.5 text-[11.5px] font-medium text-[#5f6f80] hover:bg-fill",
              screen === n && "bg-pri-l font-semibold text-pri-d",
            )}
          >
            <Icon className="size-[22px]" />
            {label}
          </button>
        ))}
        <a
          href="/legacy#/library"
          className="mt-auto flex w-[72px] flex-col items-center gap-1 rounded-2xl py-2.5 text-[11.5px] font-medium text-[#5f6f80] hover:bg-fill"
          title="Library, Create, Editor and Prepare still live in the desktop builder until they are ported"
        >
          <Library className="size-[22px]" />
          Library
        </a>
      </nav>
      <main ref={main} className="min-w-0 overflow-auto">
        <div className="mx-auto max-w-[1500px] space-y-3 px-7 py-5">
          {health && !health.vp9 && (
            <div className="rounded-xl bg-run-l px-3 py-2 text-[13px] text-run">
              ffmpeg has no libvpx-vp9, so animations cannot be encoded. Run <b className="font-mono">python -m mirsal doctor</b> for the fix.
            </div>
          )}
          <Notice />
          {screen === "inbox" && <Inbox />}
          {screen === "generate" && <Generate id={current} />}
          {screen === "video" && <VideoSheetScreen id={current} />}
          {screen === "history" && <History />}
        </div>
      </main>
    </div>
  );
}
