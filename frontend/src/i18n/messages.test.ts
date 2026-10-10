import { describe, expect, it } from "vitest";

import en from "../../messages/en.json";
import vi from "../../messages/vi.json";
import { defaultLocale, resolveLocale } from "./config";

function leaves(node: unknown, prefix = ""): [string, unknown][] {
  if (node === null || typeof node !== "object") return [[prefix, node]];
  return Object.entries(node).flatMap(([key, value]) => leaves(value, prefix ? `${prefix}.${key}` : key));
}

const flattenKeys = (node: unknown) => leaves(node).map(([key]) => key);

/** Read with `t.raw()` as form values, where an empty string is a blank field. */
const RAW_DATA = ["plan.okr.example."];

/**
 * Argument names of an ICU message, including those nested in plural/select branches.
 * Branch bodies are literal text, so `{count, plural, one {task}}` yields only `count`.
 */
function icuArguments(message: string): string[] {
  const found = new Set<string>();
  let i = 0;

  const skipSpaces = () => {
    while (/\s/.test(message[i] ?? "")) i++;
  };
  const readToken = () => {
    const start = i;
    while (i < message.length && !/[\s,{}]/.test(message[i])) i++;
    return message.slice(start, i);
  };
  const skipBlock = () => {
    for (let depth = 1; i < message.length && depth > 0; i++) {
      if (message[i] === "{") depth++;
      else if (message[i] === "}") depth--;
    }
  };

  const readText = () => {
    while (i < message.length && message[i] !== "}") {
      if (message[i] === "{") {
        i++;
        readArgument();
      } else i++;
    }
  };

  const readArgument = () => {
    skipSpaces();
    found.add(readToken());
    skipSpaces();
    if (message[i] === "}") {
      i++;
      return;
    }
    i++; // ","
    skipSpaces();
    const type = readToken();
    skipSpaces();
    if (!["plural", "select", "selectordinal"].includes(type)) {
      skipBlock();
      return;
    }
    i++; // ","
    for (;;) {
      skipSpaces();
      if (i >= message.length || message[i] === "}") {
        i++;
        return;
      }
      readToken();
      skipSpaces();
      i++; // "{"
      readText();
      i++; // "}"
    }
  };

  readText();
  return [...found].sort();
}

describe("messages", () => {
  it("vi and en expose the same keys", () => {
    expect(flattenKeys(en).sort()).toEqual(flattenKeys(vi).sort());
  });

  it.each([
    ["vi", vi],
    ["en", en],
  ])("%s has no empty messages", (_, messages) => {
    const empty = leaves(messages).filter(
      ([key, value]) => !RAW_DATA.some((prefix) => key.startsWith(prefix)) && (typeof value !== "string" || value.trim() === ""),
    );
    expect(empty.map(([key]) => key)).toEqual([]);
  });

  it("vi and en use the same message arguments", () => {
    const enMessages = new Map(leaves(en));
    const mismatched = leaves(vi)
      .filter(([key, value]) => {
        const other = enMessages.get(key);
        return typeof value === "string" && typeof other === "string" && icuArguments(value).join() !== icuArguments(other).join();
      })
      .map(([key]) => key);
    expect(mismatched).toEqual([]);
  });
});

describe("icuArguments", () => {
  it("reads simple and formatted arguments", () => {
    expect(icuArguments("{done}/{total} · {when, date, short}")).toEqual(["done", "total", "when"]);
  });

  it("ignores literal text inside plural branches", () => {
    expect(icuArguments("{count, plural, one {Show # more task} other {Show # more tasks}}")).toEqual(["count"]);
  });

  it("finds arguments nested in branches", () => {
    expect(icuArguments("{count, plural, =0 {none} other {# tasks by {date}}}")).toEqual(["count", "date"]);
  });
});

describe("resolveLocale", () => {
  it("keeps supported locales", () => {
    expect(resolveLocale("en")).toBe("en");
    expect(resolveLocale("vi")).toBe("vi");
  });

  it("falls back to the default locale", () => {
    expect(resolveLocale("fr")).toBe(defaultLocale);
    expect(resolveLocale(undefined)).toBe(defaultLocale);
  });
});
