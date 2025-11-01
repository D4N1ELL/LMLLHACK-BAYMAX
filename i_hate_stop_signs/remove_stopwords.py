import sys, re
from pathlib import Path

NORMALIZE_LOWERCASE = False
KEEP_NEGATIONS = True

DEFAULT_STOP = {
    "the","a","an","and","or","to","of","in","on","for","with","as","at",
    "by","from","that","this","it","its","be","are","is","was","were","am",
    "i","you","he","she","we","they","them","their","our","your","my","me"
}
NEGATIONS = {"not","no","nor"}

try:
    from nltk.corpus import stopwords
    STOP = set(stopwords.words("english"))
except Exception:
    STOP = set(DEFAULT_STOP)

if KEEP_NEGATIONS:
    STOP -= NEGATIONS

PUNCT = {".", ",", ";", ":", "!", "?"}
TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*|[.,;:!?]")

def clean_line(line: str) -> str:
    s = line if not NORMALIZE_LOWERCASE else line.lower()
    tokens = TOKEN_RE.findall(s)
    out = []
    for tok in tokens:
        if tok in PUNCT:
            out.append(tok)
            continue
        if tok.strip() and tok.lower() in STOP:
            continue
        out.append(tok)
    out_text = ""
    for t in out:
        if t in PUNCT:
            out_text = out_text.rstrip() + t
        else:
            out_text += ("" if out_text == "" else " ") + t
    return re.sub(r"[ \t]{2,}", " ", out_text).strip()

def clean_text(text: str) -> str:
    return "\n".join(clean_line(ln) for ln in text.splitlines())

if __name__ == "__main__":
    in_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("input.txt")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output.txt")
    raw = in_path.read_text(encoding="utf-8")
    cleaned = clean_text(raw)
    out_path.write_text(cleaned, encoding="utf-8")
    print(f"[✓] Cleaned -> {out_path}")
