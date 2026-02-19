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

                    well_name = re.search(r"Well Name and Number.*\n+(.+)", left_text)
                    well_name = well_name.group(1) if well_name else None
                    well_file_num = re.search(r"Well File No\.?\s*\n+(\d+)", right_text)
                    well_file_num = well_file_num.group(1) if well_file_num else None
                    operator = re.search(r"Operator.*\n+(.+)", left_text)
                    operator = operator.group(1) if operator else None

                    print(f"\nEXTRACTED INFO ({filename})")
                    print(f"Well Name: {well_name}")
                    print(f"File Num: {well_file_num}")
                    print(f"Operator: {operator}")
                    print(f"Extracted from {filename} page {i + 1}")
                    break
            
            # print(left_text)
            # print("==========")
            # print(right_text)
            output.append([
                str(filename),
                well_file_num,
                well_name,
                operator
            ])
        
        # temp
        ITER += 1
        if ITER == 3:
            break
    columns=["pdf", "file_num", "well_name", "operator"]
    output = pd.DataFrame(output, columns=columns)
    output.to_csv("output.csv", index=False)
    print(f"Execution time: {time.time() - start:2f} seconds")
if __name__ == "__main__":
    main()