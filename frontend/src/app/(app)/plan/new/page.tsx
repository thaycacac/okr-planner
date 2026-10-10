import { QuarterStep } from "@/components/plan/quarter-step";

export default async function PlanQuarterPage({ searchParams }: PageProps<"/plan/new">) {
  const { q } = await searchParams;
  return <QuarterStep initial={typeof q === "string" ? q : undefined} />;
}
