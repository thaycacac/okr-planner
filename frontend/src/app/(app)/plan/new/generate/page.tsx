import { redirect } from "next/navigation";

import { GenerateStep } from "@/components/plan/generate-step";

export default async function PlanGeneratePage({ searchParams }: PageProps<"/plan/new/generate">) {
  const { job } = await searchParams;
  if (typeof job !== "string" || !job) redirect("/plan/new");
  return <GenerateStep key={job} jobId={job} />;
}
