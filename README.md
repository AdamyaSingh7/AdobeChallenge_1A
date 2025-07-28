# ADOBE ROUND 1A

A lightweight PDF outline extractor that identifies document headings and generates a JSON outline of title, levels, text, and page number.

- **Multilingual Support:** Works seamlessly on PDFs in multiple languages (e.g., English, French, Chinese, German).
- **High Performance:** Processes documents up to 50 pages in under 5–6 seconds on average.

## Approach

1. **Text and Feature Extraction**

   - Use **PyMuPDF** (`fitz`) to parse each PDF page into text blocks and lines.
   - For each line, extract raw features such as font size, position (`x0`, `y0`), text length, uppercase ratio, bold/italic flags, numeric or punctuation patterns, and title-case flag.

2. **Batch Predictions for Heading Detection**

   - Aggregate all line features into a single **Pandas** DataFrame.
   - Perform a single `heading_model.predict()` over the entire DataFrame to flag heading lines.
   - This reduces per-line DataFrame construction and model-call overhead, improving performance on large documents.

3. **Merge Split/Overlapping Lines**

   - Iteratively merge consecutive fragments if they have the same font size and their vertical positions (`y0`) fall within a threshold.
   - Prevent duplicate text fragments by checking if the new fragment is already contained in the current heading entry.

## Post-Processing

4. **Map Font Sizes to Heading Levels (H1–H6)**

   - Identify the unique font sizes among detected headings in descending order.
   - Assign the largest font size to `H1`, the second-largest to `H2`, and so on up to `H6`.

5. **De-duplicate and Finalize Outline**

   - Remove any remaining duplicate heading texts.
   - Select the first `H1` as the document title.
   - Produce a JSON outline containing a `title` string and an array of `{ level, text, page }` objects.

## Models & Libraries Used

- **Models**

  - `heading_classifier.pkl`: Binary classifier (e.g., Random Forest or Logistic Regression) to detect heading vs. body text.
  - `level_classifier.pkl`: Multiclass model for heading levels; currently provided for extensibility but not used in the main batch pipeline.

- **Python Libraries**

  - [PyMuPDF](https://pypi.org/project/PyMuPDF/) (`fitz`) for PDF parsing.
  - [Pandas](https://pandas.pydata.org/) for DataFrame-based batching.
  - [scikit-learn](https://scikit-learn.org/) for loading and predicting with pre-trained models.
  - [joblib](https://joblib.readthedocs.io/) for efficient model serialization and loading.

## Prerequisites

- **Docker** installed (version 20+).
- **Python** 3.8 or later (for local testing).
- Python dependencies listed in `requirements.txt`:
  ```
  PyMuPDF
  pandas
  scikit-learn
  joblib
  ```

## Build & Run

### Build Docker Image

**In Bash (build):**

```bash
docker build --platform linux/amd64 -t adobe1a-outline-extractor:latest .
```

**In PowerShell (build):**

```powershell
docker build --platform linux/amd64 -t adobe1a-outline-extractor:latest .
```

### Run Container

**In Bash (run):**

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  adobe1a-outline-extractor:latest
```

**In PowerShell (run):**

```powershell
docker run --rm `
  -v "${PWD}\input:/app/input" `
  -v "${PWD}\output:/app/output" `
  --network none `
  adobe1a-outline-extractor:latest
```

The tool will process all PDFs in `/app/input` and write JSON outlines to `/app/output`.

> **Note:** The `/input` folder also includes extra test PDFs beyond the Adobe-provided samples:
>
> - A **50-page** document to benchmark performance.
> - A **German-language** PDF to validate multilingual support.

