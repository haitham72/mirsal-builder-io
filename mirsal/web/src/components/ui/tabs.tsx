import * as RT from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

export const Tabs = RT.Root;
export const TabsContent = RT.Content;
export const TabsList = ({ className, ...p }: RT.TabsListProps) => (
  <RT.List className={cn("inline-flex gap-1 rounded-xl bg-fill p-1", className)} {...p} />
);
export const TabsTrigger = ({ className, ...p }: RT.TabsTriggerProps) => (
  <RT.Trigger
    className={cn("rounded-lg px-3 py-1 text-[13px] font-semibold text-mut data-[state=active]:bg-sf data-[state=active]:text-tx data-[state=active]:shadow-sm", className)}
    {...p}
  />
);
