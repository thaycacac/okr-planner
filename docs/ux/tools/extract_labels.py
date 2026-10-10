"""Extract every "vi¦en" label from the wireframes into docs/ux/i18n-labels.md.

Usage: python3 docs/ux/tools/extract_labels.py
"""
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEP = "\u00a6"
INLINE = re.compile(r"\{([^{}¦]*)¦([^{}]*)\}")
JS_PAIR = re.compile(r"([^'\"<>]+)¦([^'\"<>]+)")
PAGES = [("wave1", "Đợt 1 — MVP"), ("wave2", "Đợt 2 — hoàn thiện giai đoạn 1")]


def pairs_from_text(text):
    if SEP not in text:
        return []
    if INLINE.search(text):
        return [(vi.strip(), en.strip()) for vi, en in INLINE.findall(text)]
    vi, en = text.split(SEP, 1)
    return [(vi.strip(), en.strip())]


SKIP_CLASSES = {"notes", "cap", "doc-header"}
VOID = {"meta", "link", "br", "img", "input", "hr"}


class Collector(HTMLParser):
    """Collects UI labels per section, skipping designer annotations."""

    def __init__(self):
        super().__init__()
        self.section = None
        self.titles = {}
        self.by_section = {}
        self._in_h2 = False
        self._skip = [False]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        if tag == "section" and "screen" in classes:
            self.section = a.get("id")
            self.by_section.setdefault(self.section, [])
        if tag == "h2":
            self._in_h2 = True
        if tag not in VOID:
            self._skip.append(self._skip[-1] or tag == "header" or bool(classes & SKIP_CLASSES))
        if self.section and not self._skip[-1]:
            for key in ("placeholder", "title", "aria-label"):
                if a.get(key):
                    self._add(pairs_from_text(a[key]))

    def handle_endtag(self, tag):
        if tag == "h2":
            self._in_h2 = False
        if tag not in VOID and len(self._skip) > 1:
            self._skip.pop()

    def handle_data(self, data):
        if not self.section:
            return
        found = pairs_from_text(data)
        if self._in_h2 and found and self.section not in self.titles:
            self.titles[self.section] = found[0][0]
        if not self._skip[-1]:
            self._add(found)

    def _add(self, found):
        if self.section == "flow":
            return
        bucket = self.by_section[self.section]
        for pair in found:
            if pair[0] and pair not in bucket:
                bucket.append(pair)


def esc(s):
    return s.replace("|", "\\|")


def main():
    out = [
        "# Nhãn UI song ngữ (vi / en)",
        "",
        "Sinh tự động từ wireframe bằng `python3 docs/ux/tools/extract_labels.py` — không sửa tay.",
        "Nhãn trong wireframe là nguồn chuẩn; Frontend đặt key next-intl theo màn (VD `okrForm.addKr`).",
        "Chuỗi có số liệu mẫu (giờ, ngày, tên OKR) là ví dụ: thay bằng tham số ICU (`{hours}h`, `{date}`).",
        "",
        "## Khung ứng dụng (topbar, sidebar, tab bar)",
        "",
        "| vi | en |",
        "|---|---|",
    ]
    shell = []
    js = (ROOT / "wireframes" / "wf.js").read_text(encoding="utf-8")
    js = js[js.index("const FEAS"):]
    for vi, en in JS_PAIR.findall(js):
        pair = (vi.strip(), en.strip())
        if pair not in shell:
            shell.append(pair)
    out += [f"| {esc(vi)} | {esc(en)} |" for vi, en in shell]
    for page, label in PAGES:
        path = ROOT / "wireframes" / f"{page}.html"
        if not path.exists():
            continue
        c = Collector()
        c.feed(path.read_text(encoding="utf-8"))
        out += ["", f"## {label}"]
        for sid, pairs in c.by_section.items():
            if not pairs:
                continue
            out += ["", f"### {sid.upper()} — {c.titles.get(sid, '')}", "", "| vi | en |", "|---|---|"]
            out += [f"| {esc(vi)} | {esc(en)} |" for vi, en in pairs]
    (ROOT / "i18n-labels.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote docs/ux/i18n-labels.md")


if __name__ == "__main__":
    main()
