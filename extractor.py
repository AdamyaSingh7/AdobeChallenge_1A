import fitz            # PyMuPDF
import joblib
import pandas as pd

# Paths to your trained models
HEADING_MODEL_PATH = "models/heading_classifier.pkl"
LEVEL_MODEL_PATH   = "models/level_classifier.pkl"

# Map the level‐classifier’s integer outputs to the heading labels
# (we leave this here untouched, but won’t actually use it)
CLASS_MAP_LEVEL = {
    1: "H1",
    2: "H2",
    3: "H3"
}

# These names must exactly match the columns expected by your ColumnTransformer
FEATURE_NAMES = [
    "font_size",
    "x0",
    "y0",
    "text_length",
    "uppercase_ratio",
    "is_bold",
    "is_italic",
    "starts_with_number",
    "ends_with_colon",
    "title_case"
]

def extract_features(text, font_size, x0, y0, is_bold, is_italic):
    """
    Returns a feature list in the same order as FEATURE_NAMES:
    [font_size, x0, y0, text_length, uppercase_ratio,
     is_bold, is_italic, starts_with_number, ends_with_colon, title_case]
    """
    text_length        = len(text)
    uppercase_ratio    = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    starts_with_number = int(text[:1].isdigit())
    ends_with_colon    = int(text.endswith(":"))
    title_case_flag    = int(text.istitle())

    return [
        font_size,
        x0,
        y0,
        text_length,
        uppercase_ratio,
        is_bold,
        is_italic,
        starts_with_number,
        ends_with_colon,
        title_case_flag
    ]

def extract_outline(pdf_path):
    # Load models once
    heading_model = joblib.load(HEADING_MODEL_PATH)
    level_model   = joblib.load(LEVEL_MODEL_PATH)

    doc = fitz.open(pdf_path)

    # --- PART 1: Gather *all* lines' features + metadata ---
    all_feats = []
    all_meta  = []
    for page_num, page in enumerate(doc, start=1):
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                spans = line.get("spans", [])
                if not spans:
                    continue

                text = "".join(span["text"] for span in spans).strip()
                if not text:
                    continue

                span0     = spans[0]
                font_size = span0["size"]
                font_name = span0["font"]
                flags     = span0.get("flags", 0)
                is_bold   = int(bool(flags & 0x20) or "bold" in font_name.lower())
                is_italic = int(bool(flags & 0x02))
                x0, y0, x1, y1 = line["bbox"]

                raw_feats = extract_features(
                    text=text,
                    font_size=font_size,
                    x0=x0,
                    y0=y0,
                    is_bold=is_bold,
                    is_italic=is_italic
                )

                all_feats.append(raw_feats)
                all_meta.append({
                    "text": text,
                    "page": page_num,
                    "font_size": font_size,
                    "y0": y0
                })

    # If no text at all:
    if not all_feats:
        return {"title": "", "outline": []}

    # --- PART 2: Batch‐predict which are headings ---
    X = pd.DataFrame(all_feats, columns=FEATURE_NAMES)
    is_heading_arr = heading_model.predict(X)

    # Filter down to only those marked as headings
    headings = [
        meta for meta, is_h in zip(all_meta, is_heading_arr) 
                if is_h
    ]

    # --- PART 3: Merge split/overlapping heading fragments ---
    merged = []
    for h in headings:
        if (merged
            and merged[-1]["page"]     == h["page"]
            and merged[-1]["font_size"] == h["font_size"]
            and abs(h["y0"] - merged[-1]["y0"]) < h["font_size"] * 1.5
        ):
            prev = merged[-1]
            # only append if this fragment isn't already inside
            if h["text"] not in prev["text"]:
                prev["text"] += " " + h["text"]
            prev["y0"] = h["y0"]
        else:
            merged.append(h)

    # --- PART 4: Map font‐sizes → H1..H6 and de-dup final texts ---
    unique_sizes = sorted({h["font_size"] for h in merged}, reverse=True)
    size_to_level = {
        size: f"H{idx+1}"
        for idx, size in enumerate(unique_sizes[:6])
    }

    outline    = []
    doc_title  = ""
    seen_texts = set()

    for h in merged:
        text = h["text"]
        if text in seen_texts:
            continue
        seen_texts.add(text)

        level = size_to_level.get(h["font_size"], "H6")
        if level == "H1" and not doc_title:
            doc_title = text

        outline.append({
            "level": level,
            "text": text,
            "page": h["page"]
        })

    return {"title": doc_title, "outline": outline}
