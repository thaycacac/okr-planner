import { redirect } from "next/navigation";

import { OkrStep } from "@/components/plan/okr-step";
import { parseQuarterSlug } from "@/lib/plan/quarter";

export default async function PlanOkrPage({ searchParams }: PageProps<"/plan/new/okr">) {
  const quarter = parseQuarterSlug((await searchParams).q);
  if (!quarter) redirect("/plan/new");
  return <OkrStep quarter={quarter} />;
}
