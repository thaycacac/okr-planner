import { TaskTree } from "@/components/plan/task-tree";

export default async function QuarterTasksPage({ searchParams }: PageProps<"/q/[quarter]/tasks">) {
  const { kr } = await searchParams;
  const krId = typeof kr === "string" && /^\d+$/.test(kr) ? Number(kr) : null;
  return <TaskTree krFilter={krId} />;
}
