import { emptyKr, emptyObjective, MAX_KEY_RESULTS, MAX_OBJECTIVES, type ObjectiveDraft } from "./okr-draft";

// Free-text OKRs such as
//   O1: Pass the B2 English exam
//   KR1: Enrol in a course around 20/10
// Objective lines start with O / Objective / Mục tiêu, key results with KR / Key result / Kết quả;
// a number and one of ":", ".", ")", "-" may follow. A bullet under an objective is a key result too.
const OBJECTIVE = /^(?:objectives?|mục\s*tiêu|obj|o)\s*\d*\s*[:.)\-–—]\s*(.+)$/iu;
const KEY_RESULT = /^(?:key\s*results?|kết\s*quả(?:\s*then\s*chốt)?|kr)\s*\d*\s*[:.)\-–—]\s*(.+)$/iu;
const BULLET = /^(?:[-*•–]|\d+[.)])\s+(.+)$/u;

export type ParsedOkrText = {
  objectives: ObjectiveDraft[];
  /** Key results or objectives beyond the limits, which were left out. */
  truncated: boolean;
};

export function parseOkrText(text: string): ParsedOkrText {
  const objectives: ObjectiveDraft[] = [];
  let truncated = false;
  // Where a plain line gets appended: the last key result, else the objective title.
  let last: "title" | "kr" | null = null;

  const current = () => objectives[objectives.length - 1];
  const startObjective = (title: string) => {
    if (objectives.length >= MAX_OBJECTIVES) {
      truncated = true;
      return false;
    }
    objectives.push({ ...emptyObjective(), title, keyResults: [] });
    last = "title";
    return true;
  };
  const addKr = (kr: string) => {
    if (objectives.length === 0 && !startObjective("")) return;
    const objective = current();
    if (objective.keyResults.length >= MAX_KEY_RESULTS) {
      truncated = true;
      return;
    }
    objective.keyResults.push({ ...emptyKr(), kind: "other", text: kr });
    last = "kr";
  };

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const kr = KEY_RESULT.exec(line);
    const objective = kr ? null : OBJECTIVE.exec(line);
    if (kr) addKr(kr[1].trim());
    else if (objective) startObjective(objective[1].trim());
    else if (objectives.length > 0 && BULLET.test(line)) addKr(BULLET.exec(line)![1].trim());
    else if (objectives.length === 0) startObjective(line);
    else if (last === "kr") {
      const krs = current().keyResults;
      krs[krs.length - 1].text += ` ${line}`;
    } else if (last === "title") current().title += ` ${line}`;
  }

  for (const objective of objectives) {
    if (objective.keyResults.length === 0) objective.keyResults.push(emptyKr());
  }
  return { objectives, truncated };
}
