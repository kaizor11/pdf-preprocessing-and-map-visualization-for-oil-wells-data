import pandas as pd
from PIL import Image
import pytesseract
import ocrmypdf
from pypdf import PdfReader
from pdf2image import convert_from_path, pdfinfo_from_path
import time
import os
import re

DATA_FOLDER_IN = "data/"
OUTPUT_FILE = "output_new.csv"

os.environ["PATH"] += r";C:\Program Files\Tesseract-OCR"
os.environ["PATH"] += r";C:\Program Files\poppler-25.12.0\Library\bin"

def well_num_backup(filename):
    """
    Use when OCR fails to recognize the Well File No. (top right of page)
    """
    m = re.search(r"\d+", filename)
    number = m.group(0) if m else None
    return number

def normalize(text):
    """
    Remove extra white space and newlines from OCR text for better regex search
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    lines = [re.sub(r" {2,}", " ", line) for line in lines]
    return "\n".join(lines)

def main():
    ITER = 0
    start = time.time()
    output = []
    for filename in os.listdir(DATA_FOLDER_IN):
        if filename.lower().endswith("pdf"):
            filepath_in = os.path.join(DATA_FOLDER_IN, filename)
            details = pdfinfo_from_path(filepath_in)
            maxpgs = details["Pages"]
            pages = convert_from_path(filepath_in, dpi=300, first_page=max(1, maxpgs-50), last_page=maxpgs) #upon visual inspection the pertinent application form is usually near the end of the document
            for i, page in enumerate(pages):
                width, height = page.size
                left_col = page.crop((0, 0, width //2, height))
                right_col = page.crop((width // 2, 0, width, height))
                top = page.crop((0, 0, width, height * 1/5))

                top_text = pytesseract.image_to_string(top)
                page_title = re.search(r"APPLICATION FOR PERMIT TO DRILL.+", top_text)
                
                if page_title:
                    left_text = pytesseract.image_to_string(left_col)
                    right_text = pytesseract.image_to_string(right_col)
                    left_text = normalize(left_text)
                    right_text = normalize(right_text)

                    well_name = re.search(r"Well Name.*\n+(.+)", left_text, re.IGNORECASE)
                    well_name = well_name.group(1) if well_name else ""
                    well_file_num = re.search(r"Well Number\.?\s*\n+(\d+)", right_text, re.IGNORECASE)
                    well_file_num = well_file_num.group(1) if well_file_num else ""
                    coords = re.search(r"Latitude of Well Head.*\n+(.+)", left_text, re.IGNORECASE)
                    if coords: 
                        txt = coords.group(1).split("|")
                        long = txt[0].strip()
                        lat = txt[1].strip()
                    else:
                        long = ""
                        lat = ""

                    print(f"\nEXTRACTED INFO ({filename})")
                    print(f"Well Name: {well_name}")
                    print(f"File Num: {well_file_num}")
                    print(f"Latitude: {lat}")
                    print(f"Longitude: {long}")
                    print(f"Extracted from {filename} page {i + 1}")

                                
                    output.append([
                            filename,
                            well_file_num,
                            well_name,
                            lat,
                            long
                    ])
                    break
            
            # print(left_text)
            # print("==========")
            # print(right_text)
        
        # temp
        # ITER += 1
        # if ITER == 10:
        #     break
    columns=["pdf", "file_num", "well_name", "latitude", "longitude"]
    output_df = pd.DataFrame(output, columns=columns)

    # fix file num
    err_cnt = 0
    for i, row in output_df.iterrows():
        m = re.search(r"\d+", row["pdf"])
        file_num_from_pdf = m.group(0) if m else None
        if row["file_num"] != file_num_from_pdf:
            err_cnt += 1
            row["file_num"] = file_num_from_pdf
    print(f"File_num mismatches: {err_cnt}")

    output_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Execution time: {((time.time() - start)/60):2f} min ({time.time() - start:2f}s)")
if __name__ == "__main__":
    main()