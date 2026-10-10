from app.planner_llm.schemas import Language, OkrInput

_VIETNAMESE_CHARS = frozenset("àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")


def detect_language(okr: OkrInput) -> Language:
    """Vietnamese when diacritics make up a noticeable share of letters, otherwise English."""
    parts: list[str] = []
    for objective in okr.objectives:
        parts.append(objective.title)
        parts.extend(kr.text for kr in objective.key_results)
    text = " ".join(parts).lower()
    letters = sum(ch.isalpha() for ch in text)
    vietnamese = sum(ch in _VIETNAMESE_CHARS for ch in text)
    if letters and vietnamese >= max(1, letters * 0.02):
        return "vi"
    return "en"
