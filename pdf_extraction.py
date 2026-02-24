import pandas as pd
import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import os
import re

DATA_FOLDER_IN  = "data/"
OUTPUT_FILE     = "output.csv"
DPI             = 300       
AUTH_SCAN_FIRST = 50        # ATUHROIZATION page usually in the first few pages
PERMIT_SCAN_LAST= 50        # PERMIT page usually in the last 50 pages
MAX_WORKERS     = 6         # CPU core count


def normalize(text):
    lines = [re.sub(r" {2,}", " ", line.strip()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)

def ocr_page(page, psm=3):
    raw = pytesseract.image_to_string(page, config=f"--psm {psm}")
    return normalize(raw)

def top_strip(page, fraction=0.25):
    w, h = page.size
    return page.crop((0, 0, w, h * fraction))

def left_col(page):
    w, h = page.size
    return page.crop((0, 0, w // 2, h))

def right_col(page):
    w, h = page.size
    return page.crop((w // 2, 0, w, h))

def extract_auth_fields(page):
    l_text = ocr_page(left_col(page))
    r_text = ocr_page(right_col(page))

    well_name = re.search(r"Well Name and Number.*\n+(.+)", l_text, re.IGNORECASE)
    file_num  = re.search(r"Well File No\.?\s*\n+(\d+)", r_text, re.IGNORECASE)
    operator = re.search(r"Operator.*\n+(.+)", l_text, re.IGNORECASE)

    return {
        "well_name": well_name.group(1).strip() if well_name else "",
        "file_num":  file_num.group(1).strip()  if file_num  else "",
        "operator": operator.group(1).strip() if operator else ""
    }

def extract_permit_fields(page):
    l_text = ocr_page(left_col(page))
    
    # Debug: print what's around the keyword
    idx = l_text.lower().find("latitude")
    if idx != -1:
        print(repr(l_text[idx:idx+200]))
    else:
        print("'latitude' not found in l_text at all")

    coords = re.search(r"Latitude of Well Head.*\n+(.+)", l_text, re.IGNORECASE)
    if coords:
        parts = coords.group(1).split("|")
        return {
            "latitude": parts[0].strip() if len(parts) > 0 else "",
            "longitude":  parts[1].strip() if len(parts) > 1 else "",
        }
    return {"latitude": "", "longitude": ""}

def extract_api(page):
    full_text = ocr_page(page)
    m = re.search(r"\d{2}-\d{3}-\d{5}", full_text)
    return m.group(0) if m else ""

def is_auth_page(top_text):
    return bool(re.search(r"AUTHORIZATION TO PURCHASE", top_text, re.IGNORECASE))

def is_permit_page(top_text):
    return bool(re.search(r"APPLICATION FOR PERMIT TO DRILL", top_text, re.IGNORECASE))

def process_pdf(filepath):
    """
      - Scan first AUTH_SCAN_FIRST pages for AUTHORIZATION form  → well_name, file_num, operator
      - Scan last PERMIT_SCAN_LAST pages for PERMIT TO DRILL form → lat, long
      - Scan all pages top strip for API# → stop at first match
    """
    filename = os.path.basename(filepath)
    record = {
        "pdf":       filename,
        "file_num":  "",
        "well_name": "",
        "operator":  "",
        "api":       "",
        "latitude":  "",
        "longitude": "",
        "flags":     [],
    }

    try:
        details = pdfinfo_from_path(filepath)
        maxpgs  = details["Pages"]

        # authorization form fields
        auth_end   = min(AUTH_SCAN_FIRST, maxpgs)
        auth_pages = convert_from_path(filepath, dpi=DPI, first_page=1, last_page=auth_end)

        for i, page in enumerate(auth_pages):
            top_text = ocr_page(top_strip(page))
            if is_auth_page(top_text):
                fields = extract_auth_fields(page)
                record["well_name"] = fields["well_name"]
                record["file_num"]  = fields["file_num"]
                record["operator"]  = fields["operator"]
                print(f"  [{filename}] AUTH found on page {i+1} — {fields}")
                break  # only need first occurrence

        # permit form fields
        permit_start = max(1, maxpgs - PERMIT_SCAN_LAST)
        permit_pages = convert_from_path(filepath, dpi=DPI, first_page=permit_start, last_page=maxpgs)

        for i, page in enumerate(permit_pages):
            top_text = ocr_page(top_strip(page))
            if is_permit_page(top_text):
                fields = extract_permit_fields(page)
                record["latitude"]  = fields["latitude"]
                record["longitude"] = fields["longitude"]
                print(f"  [{filename}] PERMIT found on page {permit_start+i} — {fields}")
                break  # only need first occurrence

        # api
        for page in auth_pages:
            api = extract_api(top_strip(page, fraction=0.4))
            if api:
                record["api"] = api
                break

        if not record["api"]:
            # not in first 50, scan remaining pages top strip only
            remaining_start = auth_end + 1
            if remaining_start <= maxpgs:
                remaining = convert_from_path(
                    filepath, dpi=DPI,
                    first_page=remaining_start,
                    last_page=maxpgs
                )
                for page in remaining:
                    api = extract_api(top_strip(page, fraction=0.4))
                    if api:
                        record["api"] = api
                        break

        # flags for debug
        for field in ["file_num", "well_name", "operator", "api", "latitude", "longitude"]:
            if not record[field]:
                record["flags"].append(f"MISSING:{field}")

        # fallback for file_num: use file name
        if not record["file_num"]:
            m = re.search(r"\d+", filename)
            if m:
                record["file_num"] = m.group(0)
                record["flags"].append("file_num:FROM_FILENAME")

    except Exception as e:
        record["flags"].append(f"ERROR:{str(e)}")
        print(f"  [{filename}] ERROR: {e}")

    record["flags"] = "|".join(record["flags"]) if record["flags"] else "OK"
    print(f"  [{filename}] Final record: {record}")
    return record

def main():
    start = time.time()

    pdf_files = [
        os.path.join(DATA_FOLDER_IN, f)
        for f in os.listdir(DATA_FOLDER_IN)
        if f.lower().endswith(".pdf")
    ]

    results = []

    # parallel process with CPU cores
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_pdf, fp): fp for fp in pdf_files}
        for future in as_completed(futures):
            filepath = futures[future]
            try:
                record = future.result()
                results.append(record)
            except Exception as e:
                print(f"Failed to process {filepath}: {e}")
                results.append({
                    "pdf": os.path.basename(filepath),
                    "file_num": "", "well_name": "", "api": "",
                    "latitude": "", "longitude": "",
                    "flags": f"FATAL_ERROR:{e}"
                })

    # summary report
    df = pd.DataFrame(results)
    ok_count      = (df["flags"] == "OK").sum()
    missing_count = df["flags"].str.contains("MISSING").sum()
    error_count   = df["flags"].str.contains("ERROR").sum()
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"  Total PDFs:      {len(df)}")
    print(f"  Fully extracted: {ok_count}")
    print(f"  Missing fields:  {missing_count}")
    print(f"  Errors:          {error_count}")
    print(f"{'='*50}")
    print(df[df["flags"] != "OK"][["pdf", "flags"]])

    # output CSVs
    columns = ["pdf", "file_num", "well_name", "operator", "api", "latitude", "longitude"]    
    df[columns].to_csv(OUTPUT_FILE, index=False)
    df[["pdf", "flags"]].to_csv("flag_output.csv", index=False)

    elapsed = time.time() - start
    print(f"\nSaved to {OUTPUT_FILE} and flag_output.csv")
    print(f"Execution time: {elapsed/60:.2f} min ({elapsed:.1f}s)")

if __name__ == "__main__":
    main()