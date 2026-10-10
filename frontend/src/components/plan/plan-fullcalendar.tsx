"use client";

import type {
  DayCellContentArg,
  DayHeaderContentArg,
  EventContentArg,
  EventDropArg,
  EventInput,
  MoreLinkContentArg,
} from "@fullcalendar/core";
import viLocale from "@fullcalendar/core/locales/vi";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin, { Draggable, type DropArg } from "@fullcalendar/interaction";
import FullCalendar from "@fullcalendar/react";
import { useLocale, useTranslations } from "next-intl";
import { type ReactNode, useEffect, useMemo, useRef } from "react";
import { cn } from "cn";

import type { ScheduleDay } from "@/lib/api/types";
import type { CalendarBlock, KrMarker } from "@/lib/plan/plan-view";

export type PlanFullCalendarProps = {
  mode: "week" | "month";
  /** Monday of the week, or the first day of the month. */
  date: string;
  blocks: readonly CalendarBlock[];
  markers: readonly KrMarker[];
  days: ReadonlyMap<string, ScheduleDay>;
  /** Blocks render their own button: FullCalendar events without a URL are not focusable. */
  renderBlock: (block: CalendarBlock) => ReactNode;
  renderMarker: (marker: KrMarker) => ReactNode;
  renderHeader?: (date: string) => ReactNode;
  renderCell: (date: string, inMonth: boolean) => ReactNode;
  renderMore?: (count: number) => ReactNode;
  canDrop: (date: string) => boolean;
  /** Returns false when the move failed, so the chip snaps back. */
  onMove: (taskId: number, date: string) => Promise<boolean>;
  onMore?: (date: string) => void;
  /** Container whose `[data-drag-task]` children can be dropped onto a day. */
  trayId?: string;
};

const isoOf = (date: Date) => date.toISOString().slice(0, 10);

export default function PlanFullCalendar({
  mode,
  date,
  blocks,
  markers,
  days,
  renderBlock,
  renderMarker,
  renderHeader,
  renderCell,
  renderMore,
  canDrop,
  onMove,
  onMore,
  trayId,
}: PlanFullCalendarProps) {
  const ref = useRef<FullCalendar>(null);
  const locale = useLocale();
  const t = useTranslations("plan.calendar");

  useEffect(() => {
    ref.current?.getApi().gotoDate(date);
  }, [date]);

  useEffect(() => {
    const tray = trayId ? document.getElementById(trayId) : null;
    if (!tray) return;
    const draggable = new Draggable(tray, {
      itemSelector: "[data-drag-task]",
      eventData: (el) => ({ create: false, title: el.dataset.dragTitle ?? "" }),
    });
    return () => draggable.destroy();
  }, [trayId]);

  const events = useMemo<EventInput[]>(
    () => [
      ...markers.map((marker) => ({
        id: `m-${marker.krId}`,
        start: marker.date,
        allDay: true,
        order: -1,
        editable: false,
        backgroundColor: "transparent",
        borderColor: "transparent",
        extendedProps: { marker },
      })),
      ...blocks.map((block, order) => ({
        id: block.id,
        start: block.date,
        allDay: true,
        order,
        editable: !block.view.done,
        backgroundColor: "transparent",
        borderColor: "transparent",
        extendedProps: { block },
      })),
    ],
    [blocks, markers],
  );

  async function handleDrop(arg: EventDropArg) {
    const block = arg.event.extendedProps.block as CalendarBlock | undefined;
    const target = arg.event.start ? isoOf(arg.event.start) : null;
    if (!block || !target) return arg.revert();
    if (!(await onMove(block.view.task.id, target))) arg.revert();
  }

  function handleExternalDrop(arg: DropArg) {
    const taskId = Number(arg.draggedEl.dataset.dragTask);
    if (Number.isFinite(taskId)) void onMove(taskId, isoOf(arg.date));
  }

  return (
    <div className={cn("okr-calendar", mode === "month" && "okr-calendar-month")}>
      <FullCalendar
        ref={ref}
        plugins={[dayGridPlugin, interactionPlugin]}
        initialView={mode === "month" ? "dayGridMonth" : "dayGridWeek"}
        key={mode}
        initialDate={date}
        timeZone="UTC"
        locales={[viLocale]}
        locale={locale}
        // FullCalendar's own a11y hints are English-only, even in its vi locale.
        moreLinkHint={(count: number) => t("moreHint", { count })}
        firstDay={1}
        headerToolbar={false}
        height="auto"
        fixedWeekCount={false}
        showNonCurrentDates
        dayMaxEvents={mode === "month" ? 3 : false}
        eventOrder="order"
        events={events}
        editable
        eventDurationEditable={false}
        droppable={trayId !== undefined}
        eventAllow={(span) => canDrop(isoOf(span.start))}
        dropAccept={(el) => el instanceof HTMLElement && el.dataset.dragTask !== undefined}
        eventDrop={(arg) => void handleDrop(arg)}
        drop={handleExternalDrop}
        moreLinkContent={(arg: MoreLinkContentArg) => (renderMore ? renderMore(arg.num) : `+${arg.num}`)}
        moreLinkClick={(arg) => {
          onMore?.(isoOf(arg.date));
        }}
        dayHeaderContent={
          renderHeader ? (arg: DayHeaderContentArg) => renderHeader(isoOf(arg.date)) : undefined
        }
        dayCellClassNames={(arg) => {
          const day = days.get(isoOf(arg.date));
          if (!day) return ["okr-day-outside"];
          if (day.off_reason === "holiday") return ["okr-day-holiday"];
          if (day.off_reason === "leave") return ["okr-day-leave"];
          if (day.off_reason) return ["okr-day-off"];
          return day.is_buffer ? ["okr-day-buffer"] : [];
        }}
        dayCellContent={(arg: DayCellContentArg) => renderCell(isoOf(arg.date), !arg.isOther)}
        eventContent={(arg: EventContentArg) => {
          const { block, marker } = arg.event.extendedProps as { block?: CalendarBlock; marker?: KrMarker };
          if (marker) return renderMarker(marker);
          return block ? renderBlock(block) : null;
        }}
      />
    </div>
  );
}
