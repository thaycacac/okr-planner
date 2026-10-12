import type { components } from "./schema";

type Schemas = components["schemas"];

export type ErrorDetail = Schemas["ErrorDetail"];
export type ErrorResponse = Schemas["ErrorResponse"];
export type CalendarSettings = Schemas["CalendarSettings"];
export type WeekdayCapacity = Schemas["WeekdayCapacity"];
export type Weekday = keyof WeekdayCapacity;
export type LlmProviderName = Schemas["LlmProviderName"];
export type LocalApiStyle = Schemas["LocalApiStyle"];
export type LlmSettings = Schemas["LlmSettings"];
export type LlmSettingsUpdate = Schemas["LlmSettingsUpdate"];
export type LlmTestRequest = Schemas["LlmTestRequest"];
export type LlmTestResult = Schemas["LlmTestResult"];
export type LlmTestErrorCode = Schemas["LlmTestErrorCode"];

export type OkrParseResult = Schemas["OkrParseResult"];

export type QuarterSummary = Schemas["QuarterSummary"];
export type QuarterDetail = Schemas["QuarterDetail"];
export type ObjectiveOut = Schemas["ObjectiveOut"];
export type ObjectivePriority = Schemas["ObjectivePriority"];
export type KeyResultOut = Schemas["KeyResultOut"];
export type KeyResultKind = Schemas["KeyResultKind"];
export type KeyResultCreate = Schemas["KeyResultCreate"];
export type TaskOut = Schemas["TaskOut"];

export type PlanCreate = Schemas["PlanCreate"];
export type PlanJob = Schemas["PlanJob"];
export type PlanRunDetail = Schemas["PlanRunDetail"];
export type PlanRunStatus = Schemas["PlanRunStatus"];
export type PlanStage = Schemas["PlanStage"];
export type PlanStepTrace = Schemas["PlanStepTrace"];
export type PlanEvent = Schemas["PlanEvent"];
export type PlanFailure = Schemas["PlanFailure"];
export type PlanFailureCode = Schemas["PlanFailureCode"];
export type ClarificationQuestion = Schemas["ClarificationQuestion"];

export type QuarterSchedule = Schemas["QuarterSchedule"];
export type ScheduledTaskOut = Schemas["ScheduledTaskOut"];
export type ScheduleDay = Schemas["ScheduleDay"];
export type AllocationOut = Schemas["AllocationOut"];
export type FeasibilityOut = Schemas["FeasibilityOut"];
export type FeasibilityStatus = Schemas["FeasibilityStatus"];
export type DayOffReason = Schemas["DayOffReason"];

export type TaskCreate = Schemas["TaskCreate"];
export type TaskUpdate = Schemas["TaskUpdate"];
export type PinnedDay = Schemas["PinnedDay"];
export type RescheduleAction = Schemas["RescheduleAction"];
export type RescheduleResult = Schemas["RescheduleResult"];
export type PinConflict = Schemas["PinConflict"];
export type PinConflictCode = Schemas["PinConflictCode"];
export type TaskDateChange = Schemas["TaskDateChange"];

export type KeyResultMilestones = Schemas["KeyResultMilestones"];
export type MilestoneCheckpoint = Schemas["MilestoneCheckpoint"];

export type OverloadOptions = Schemas["OverloadOptions"];
export type OverloadOption = Schemas["OverloadOption"];
export type OptionOutcome = Schemas["OptionOutcome"];
export type OptionEffect = Schemas["OptionEffect"];
export type OptionEvaluation = Schemas["OptionEvaluation"];
export type OptionApplication = Schemas["OptionApplication"];
export type OptionGroup = Schemas["OptionGroup"];
export type WeekdayHint = Schemas["WeekdayHint"];

export type LeaveDayOut = Schemas["LeaveDayOut"];
export type HolidayOut = Schemas["HolidayOut"];
export type HolidayKind = Schemas["HolidayKind"];
export type HolidayStatus = Schemas["HolidayStatus"];
export type HolidayCreate = Schemas["HolidayCreate"];

export type ExportFormat = Schemas["ExportFormat"];
export type ExportSheet = Schemas["ExportSheet"];

export function errorDetail(error: unknown): ErrorDetail | null {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail: unknown }).detail;
    if (detail && typeof detail === "object" && "code" in detail) {
      return detail as ErrorDetail;
    }
  }
  return null;
}
