import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const button = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-xl font-semibold transition-colors disabled:opacity-45 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        pri: "bg-pri text-white shadow-[0_4px_12px_#3b82f633] hover:bg-pri-d disabled:shadow-none",
        soft: "bg-sf border border-bd text-tx hover:bg-fill",
        ok: "bg-ok text-white hover:bg-emerald-700",
        bad: "bg-sf border border-bd text-bad hover:bg-bad-l",
        ghost: "text-mut hover:bg-fill hover:text-tx",
      },
      size: { md: "h-9 px-3.5 text-[13px]", sm: "h-7 px-2.5 text-xs rounded-lg", icon: "size-8 rounded-lg" },
    },
    defaultVariants: { variant: "soft", size: "md" },
  },
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof button> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return <Comp ref={ref} className={cn(button({ variant, size }), className)} {...props} />;
});
Button.displayName = "Button";
