import pandas as pd
from PIL import Image
import pytesseract
import ocrmypdf
from pypdf import PdfReader
from pdf2image import convert_from_path
import time
import os
import re

DATA_FOLDER_IN = "data/"
OUTPUT_FILE = "output.csv"

# os.environ["PATH"] += r";C:\Program Files\Tesseract-OCR"
# os.environ["PATH"] += r";C:\Program Files\poppler\Library\bin"

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
            pages = convert_from_path(filepath_in, dpi=300, first_page=1, last_page=20)
            for i, page in enumerate(pages):
                width, height = page.size
                left_col = page.crop((0, 0, width //2, height))
                right_col = page.crop((width // 2, 0, width, height))
                top = page.crop((0, 0, width, height * 1/5))

                top_text = pytesseract.image_to_string(top)
                page_title = re.search(r"AUTHORIZATION TO PURCHASE.+", top_text)
                
                if page_title:
                    left_text = pytesseract.image_to_string(left_col)
                    right_text = pytesseract.image_to_string(right_col)
                    left_text = normalize(left_text)
                    right_text = normalize(right_text)

                    well_name = re.search(r"Well Name and Number.*\n+(.+)", left_text, re.IGNORECASE)
                    well_name = well_name.group(1) if well_name else ""
                    well_file_num = re.search(r"Well File No\.?\s*\n+(\d+)", right_text, re.IGNORECASE)
                    well_file_num = well_file_num.group(1) if well_file_num else None
                    operator = re.search(r"Operator.*\n+(.+)", left_text, re.IGNORECASE)
                    operator = operator.group(1) if operator else ""
                    address = re.search(r"Address.*\n+(.+)", left_text, re.IGNORECASE)
                    address = address.group(1) if address else ""
                    # address2 = re.search(r"City State Zip Code.*\n+(.+)", right_text, re.IGNORECASE)
                    # address2 = address2.group(1) if address2 else ""

                    print(f"\nEXTRACTED INFO ({filename})")
                    print(f"Well Name: {well_name}")
                    print(f"File Num: {well_file_num}")
                    print(f"Operator: {operator}")
                    print(f"Address: {address}")
                    print(f"Extracted from {filename} page {i + 1}")
                    break
                else:
                    print("Did not find AUTHORIZATION TO PURCHASE page")
            
            # print(left_text)
            # print("==========")
            # print(right_text)
            output.append([
                filename,
                well_file_num,
                well_name,
                operator,
                address
            ])
        
        # temp
        # ITER += 1
        # if ITER == 10:
        #     break
    columns=["pdf", "file_num", "well_name", "operator", "address"]
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
            

    output_df.to_csv("output.csv", index=False)
    print(f"Execution time: {((time.time() - start)/60):2f} min ({time.time() - start:2f}s)")
if __name__ == "__main__":
    main()