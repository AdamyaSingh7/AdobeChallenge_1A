# process_pdfs.py

import json
import argparse
from pathlib import Path

from extractor import extract_outline

def process_all_pdfs(input_dir: str, output_dir: str):
    input_path  = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for pdf_file in input_path.glob("*.pdf"):
        result = extract_outline(str(pdf_file))
        out_file = output_path / f"{pdf_file.stem}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"[✔] Wrote outline for {pdf_file.name} → {out_file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process all PDFs in a folder")
    parser.add_argument("--input",  default="input",  help="Folder with PDFs")
    parser.add_argument("--output", default="output", help="Folder for JSON outlines")
    args = parser.parse_args()

    process_all_pdfs(args.input, args.output)
