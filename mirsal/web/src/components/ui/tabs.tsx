import * as RT from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

export const Tabs = RT.Root;
export const TabsContent = RT.Content;
export const TabsList = ({ className, ...p }: RT.TabsListProps) => (
  <RT.List className={cn("inline-flex gap-2.5", className)} {...p} />
);
export const TabsTrigger = ({ className, ...p }: RT.TabsTriggerProps) => (
  <RT.Trigger
    className={cn("rounded-full bg-fill px-6 py-2 text-[14px] font-semibold text-[#4b5b6b] hover:bg-[#e5ecf2] data-[state=active]:bg-pri data-[state=active]:text-white data-[state=active]:shadow-[0_4px_12px_#3b82f633]", className)}
    {...p}
  />
);
