import { redirect } from "next/navigation";

export default async function QuarterPage({ params }: PageProps<"/q/[quarter]">) {
  const { quarter } = await params;
  redirect(`/q/${quarter}/tasks`);
}
