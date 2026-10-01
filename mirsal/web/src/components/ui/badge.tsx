import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badge = cva("inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-semibold leading-4", {
  variants: {
    tone: {
      neutral: "bg-fill text-mut",
      pri: "bg-pri-l text-pri-d",
      ok: "bg-ok-l text-ok",
      bad: "bg-bad-l text-bad",
      warn: "bg-run-l text-run",
    },
  },
  defaultVariants: { tone: "neutral" },
});

export function Badge({ tone, className, ...p }: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badge>) {
  return <span className={cn(badge({ tone }), className)} {...p} />;
}
