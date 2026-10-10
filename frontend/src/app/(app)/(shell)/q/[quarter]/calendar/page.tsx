import { Suspense } from "react";

import { PlanCalendar } from "@/components/plan/week-calendar";

export default function QuarterCalendarPage() {
  return (
    <Suspense>
      <PlanCalendar />
    </Suspense>
  );
}
