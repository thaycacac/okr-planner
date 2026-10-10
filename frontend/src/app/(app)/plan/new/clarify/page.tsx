import { redirect } from "next/navigation";

import { ClarifyStep } from "@/components/plan/clarify-step";

export default async function PlanClarifyPage({ searchParams }: PageProps<"/plan/new/clarify">) {
  const { job } = await searchParams;
  if (typeof job !== "string" || !job) redirect("/plan/new");
  return <ClarifyStep key={job} jobId={job} />;
}
