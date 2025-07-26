import os
import json
import csv
import fitz        # PyMuPDF
import argparse
import difflib

def extract_lines(pdf_path):
    """
    1) Extracts every text line from the PDF,
    2) Captures font & position features.
    """
    doc = fitz.open(pdf_path)
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] != 0:  # skip non-text
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                # join multi-span lines into one text
                text = "".join(span["text"] for span in spans).strip()
                font_size = spans[0]["size"]
                font_name = spans[0]["font"]
                flags = spans[0].get("flags", 0)
                # detect bold both by font flags and name
                is_bold = bool(flags & 0x20) or ("bold" in font_name.lower())
                is_italic = bool(flags & 0x02)
                x0, y0, x1, y1 = line["bbox"]
                yield {
                    "page_num": page_index + 1,
                    "text": text,
                    "font_size": font_size,
                    "font_name": font_name,
                    "is_bold": int(is_bold),
                    "is_italic": int(is_italic),
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                }

def load_outline(json_path):
    """
    Loads the JSON outline into a dict:
      { page_number: { ground_truth_text: level, ... }, ... }
    Also inserts the "title" as H1 on page 1.
    """
    outlines = {}
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        title = data.get("title", "").strip()
        if title:
            outlines.setdefault(1, {})[title] = "H1"
        for item in data.get("outline", []):
            page = item.get("page")
            text = item.get("text", "").strip()
            level = item.get("level", "")
            if page and text and level:
                outlines.setdefault(page, {})[text] = level
    return outlines

def assign_rule_based_levels(rows):
    """
    If a line wasn't matched via JSON, we can still
    assign H1/H2/H3 by font size ordering:
      - Largest font on that page → H1
      - 2nd largest  → H2
      - 3rd largest  → H3
    """
    from collections import defaultdict
    
    # collect unique font sizes per page
    sizes_by_page = defaultdict(set)
    for r in rows:
        sizes_by_page[r["page_num"]].add(r["font_size"])
    # map page → sorted font sizes descending
    sorted_sizes = {
        p: sorted(sizes, reverse=True) for p, sizes in sizes_by_page.items()
    }
    
    for r in rows:
        if r["is_heading"] == 0:
            page = r["page_num"]
            size_list = sorted_sizes[page]
            if not size_list:
                continue
            fs = r["font_size"]
            # find index in sorted list
            try:
                idx = size_list.index(fs)
            except ValueError:
                continue
            if idx == 0:
                r["heading_level"] = "H1"
                r["is_heading"] = 1
            elif idx == 1:
                r["heading_level"] = "H2"
                r["is_heading"] = 1
            elif idx == 2:
                r["heading_level"] = "H3"
                r["is_heading"] = 1
    return rows

def generate_csv(input_dir, output_csv):
    all_rows = []
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".pdf"):
            continue
        base, _ = os.path.splitext(fname)
        pdf_path  = os.path.join(input_dir, fname)
        json_path = os.path.join(input_dir, f"{base}.json")
        
        # load ground-truth if we have it
        outline_map = {}
        if os.path.exists(json_path):
            outline_map = load_outline(json_path)
        else:
            print(f"[WARN] No JSON outline for {fname}")

        # extract every line from the PDF
        for line in extract_lines(pdf_path):
            page = line["page_num"]
            text = line["text"]
            is_heading = 0
            heading_level = ""
            
            # first try exact/substring/fuzzy match
            if page in outline_map:
                for gt_text, level in outline_map[page].items():
                    lt, gt = text.lower(), gt_text.lower()
                    sim = difflib.SequenceMatcher(None, lt, gt).ratio()
                    if gt in lt or lt in gt or sim > 0.7:
                        is_heading = 1
                        heading_level = level
                        break
            
            all_rows.append({
                **line,
                "is_heading": is_heading,
                "heading_level": heading_level
            })
    
    # second pass: rule-based fallback for any remaining
    all_rows = assign_rule_based_levels(all_rows)

    # write CSV
    fieldnames = [
        "page_num","text","font_size","font_name",
        "is_bold","is_italic","x0","y0","x1","y1",
        "is_heading","heading_level"
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"[✔] CSV generated at: {os.path.abspath(output_csv)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract headings (H1/H2/H3) from PDFs using JSON + font rules"
    )
    parser.add_argument("input_dir", help="Folder with .pdf and .json pairs")
    parser.add_argument("output_csv", help="Where to write the dataset CSV")
    args = parser.parse_args()
    generate_csv(args.input_dir, args.output_csv)
