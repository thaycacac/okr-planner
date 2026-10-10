import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(join(import.meta.dirname, "globals.css"), "utf8");

type Oklch = { l: number; c: number; h: number };

function themeBlock(selector: string): string {
  const start = css.indexOf(`${selector} {`);
  expect(start).toBeGreaterThanOrEqual(0);
  return css.slice(start, css.indexOf("}", start));
}

function chartTokens(selector: string): Oklch[] {
  const block = themeBlock(selector);
  return [1, 2, 3, 4, 5].map((n) => {
    const match = block.match(
      new RegExp(`--chart-${n}:\\s*oklch\\(([\\d.]+) ([\\d.]+) ([\\d.]+)\\)`),
    );
    expect(match, `--chart-${n} in ${selector}`).not.toBeNull();
    const [, l, c, h] = match!;
    return { l: Number(l), c: Number(c), h: Number(h) };
  });
}

function linearSrgb({ l, c, h }: Oklch): [number, number, number] {
  const a = c * Math.cos((h * Math.PI) / 180);
  const b = c * Math.sin((h * Math.PI) / 180);
  const l3 = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m3 = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s3 = (l - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3,
    -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3,
    -0.0041960863 * l3 - 0.7034186147 * m3 + 1.707614701 * s3,
  ];
}

function contrastWithWhite(color: Oklch): number {
  const [r, g, b] = linearSrgb(color);
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return 1.05 / (luminance + 0.05);
}

describe.each([":root", ".dark"])("chart tokens in %s", (selector) => {
  const tokens = chartTokens(selector);

  it("stay inside the sRGB gamut so contrast does not depend on gamut mapping", () => {
    for (const token of tokens) {
      for (const channel of linearSrgb(token)) {
        expect(channel).toBeGreaterThanOrEqual(-1e-4);
        expect(channel).toBeLessThanOrEqual(1 + 1e-4);
      }
    }
  });

  it("keep white text at 4.5:1 or more", () => {
    for (const token of tokens) {
      expect(contrastWithWhite(token)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("are five distinct hues rather than greys", () => {
    const hues = tokens.map((t) => t.h).sort((x, y) => x - y);
    for (const token of tokens) expect(token.c).toBeGreaterThan(0.05);
    const gaps = hues.map((h, i) => (i === 0 ? h + 360 - hues[hues.length - 1] : h - hues[i - 1]));
    expect(Math.min(...gaps)).toBeGreaterThanOrEqual(30);
  });
});
