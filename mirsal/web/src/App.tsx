import { useEffect, useRef } from "react";
import { History as HistoryIcon, Inbox as InboxIcon, Layers, Library, MessageCircle, Scissors } from "lucide-react";
import { Notice } from "@/components/shared";
import { Sidebar } from "@/components/Sidebar";
import { useGenList } from "@/hooks";
import { cn } from "@/lib/utils";
import { useUI, type Screen } from "@/store";
import Generate from "@/screens/Generate";
import History from "@/screens/History";
import Inbox from "@/screens/Inbox";
import VideoSheetScreen from "@/screens/VideoSheet";

const NAV: { id: Screen; label: string; icon: typeof InboxIcon }[] = [
  { id: "inbox", label: "Inbox", icon: InboxIcon },
  { id: "generate", label: "Stickers", icon: Layers },
  { id: "video", label: "Video", icon: Scissors },
  { id: "history", label: "History", icon: HistoryIcon },
];

const TITLE: Record<Screen, string> = { inbox: "Inbox", generate: "Sticker generation", video: "Video sheet", history: "History" };

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
    <div className="grid h-full grid-cols-[96px_1fr] xl:grid-cols-[96px_360px_1fr]">
      <nav aria-label="Main" className="flex flex-col items-center gap-1.5 border-r border-bd bg-sf/70 py-3.5">
        <div className="mb-4 mt-1 grid size-10 place-items-center rounded-xl bg-pri text-white" aria-hidden>
          <MessageCircle className="size-6 fill-white/20" />
        </div>
        {NAV.map(({ id: n, label, icon: Icon }) => (
          <button
            key={n}
            aria-current={screen === n ? "page" : undefined}
            onClick={() => go(n, n === "generate" || n === "video" ? current : null)}
            className={cn(
              "flex w-[72px] flex-col items-center gap-1.5 rounded-2xl py-2.5 text-[12px] text-[#5f6f80] hover:bg-fill",
              screen === n && "bg-pri-l font-semibold text-pri-d",
            )}
          >
            <Icon className="size-6" strokeWidth={1.8} />
            {label}
          </button>
        ))}
        <a
          href="/legacy#/library"
          className="mt-auto flex w-[72px] flex-col items-center gap-1.5 rounded-2xl py-2.5 text-[12px] text-[#5f6f80] hover:bg-fill"
          title="Library, Create, Editor and Prepare still live in the desktop builder until they are ported"
        >
          <Library className="size-6" strokeWidth={1.8} />
          Library
        </a>
      </nav>
      <Sidebar current={current} />
      <section aria-label={TITLE[screen]} className="flex min-h-0 min-w-0 p-3 xl:pl-0">
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-[20px] border border-bd bg-sf shadow-[0_10px_30px_-18px_rgba(15,23,42,0.25)]">
          <header className="flex items-center gap-2.5 border-b border-bd/70 px-6 py-3.5">
            <span className="grid size-7 place-items-center rounded-lg bg-pri-l text-pri-d" aria-hidden>
              <Layers className="size-4" />
            </span>
            <p className="text-[16px] font-semibold">{TITLE[screen]}</p>
          </header>
          <main ref={main} className="min-h-0 flex-1 overflow-auto">
            <div className="mx-auto max-w-[1300px] space-y-4 px-6 py-5">
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
      </section>
    </div>
  );
}
