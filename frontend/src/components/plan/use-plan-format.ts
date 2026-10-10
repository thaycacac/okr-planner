"use client";

import { useFormatter, useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

import { utcDate, weekdayOf } from "@/lib/plan/dates";
import { hours } from "@/lib/plan/plan-view";

export function usePlanFormat() {
  const format = useFormatter();
  const locale = useLocale();
  const tDays = useTranslations("weekdaysShort");
  return useMemo(() => {
    // Intl renders vi day+month as "23-12"; Vietnamese readers expect "23/12".
    const dayMonth = (iso: string) =>
      locale === "vi"
        ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}`
        : format.dateTime(utcDate(iso), { day: "2-digit", month: "2-digit", timeZone: "UTC" });
    return {
      date: (iso: string) =>
        format.dateTime(utcDate(iso), { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" }),
      dayMonth,
      dayRange: (start: string | null, end: string | null) => {
        if (!start || !end) return "—";
        return start === end ? dayMonth(start) : `${dayMonth(start)}–${dayMonth(end)}`;
      },
      dayOfMonth: (iso: string) => iso.slice(8, 10),
      monthYear: (iso: string) =>
        locale === "vi"
          ? `Tháng ${Number(iso.slice(5, 7))}/${iso.slice(0, 4)}`
          : format.dateTime(utcDate(iso), { month: "long", year: "numeric", timeZone: "UTC" }),
      monthShort: (iso: string) =>
        locale === "vi" ? `T${Number(iso.slice(5, 7))}` : format.dateTime(utcDate(iso), { month: "short", timeZone: "UTC" }),
      weekday: (iso: string) => tDays(weekdayOf(iso)),
      hours: (minutes: number) => `${format.number(hours(minutes), { maximumFractionDigits: 1 })}h`,
      number: (value: number) => format.number(value, { maximumFractionDigits: 2 }),
      /** A KR value with its unit; "%" sticks to the number, other units follow a space. */
      quantity: (value: number, unit: string | null) => {
        const text = format.number(value, { maximumFractionDigits: 1 });
        if (!unit) return text;
        return unit.trim() === "%" ? `${text}%` : `${text} ${unit.trim()}`;
      },
      // With a year Intl uses slashes in vi too ("01/10/2026"), unlike day+month alone.
      time: (timestamp: string) => {
        const at = new Date(timestamp);
        const clock = format.dateTime(at, { hour: "2-digit", minute: "2-digit" });
        return `${clock} ${format.dateTime(at, { day: "2-digit", month: "2-digit", year: "numeric" })}`;
      },
      clock: (ms: number) =>
        format.dateTime(new Date(ms), { hour: "2-digit", minute: "2-digit" }),
    };
  }, [format, locale, tDays]);
}

export function formatElapsed(seconds: number) {
  const s = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}
