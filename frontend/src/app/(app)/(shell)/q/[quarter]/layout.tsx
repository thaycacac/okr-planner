import { notFound } from "next/navigation";

import { PlanDataProvider } from "@/components/plan/plan-data";
import { PlanShell } from "@/components/plan/plan-shell";
import { parseQuarterSlug } from "@/lib/plan/quarter";

export default async function QuarterLayout({ children, params }: LayoutProps<"/q/[quarter]">) {
  const { quarter } = await params;
  const ref = parseQuarterSlug(quarter);
  if (!ref) notFound();
  return (
    <PlanDataProvider key={quarter} quarter={ref}>
      <PlanShell>{children}</PlanShell>
    </PlanDataProvider>
  );
}
