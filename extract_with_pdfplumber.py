import os
import pdfplumber
from pathlib import Path
import pytesseract
import re
class  plumber_processor:

    # initializing the class 
    def __init__(self,folder = "./data"):
        # ./data is the path of pdf

        self.folder = Path(folder)
    
    def get_pdf_names(self,prefix ="W"):

        '''
        for file named like W1234.pdf
        returns a sorted list
        '''

        folder = self.folder
        print(f"using prefix {prefix}")
        pdf_files = folder.glob(f"{prefix}*.pdf")
        print()
       
        try:

            sorted_files = sorted(pdf_files, key=lambda p: int(p.stem[len(prefix):]))

        except ValueError as e:

            print("formatting error!")
            return []
        

        #return first 10 filenames 
        for f in sorted_files[:10]:
            print(f.name)


        return sorted_files
    
    def get_pdf_overview(self, pdf_path):
        stats = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
               
                table_details = []
                for t in tables:
                
                    header = t[0][:3] if t else []
                    table_details.append({
                        "rows": len(t),
                        "header": header
                    })
                
                stats.append({
                    "page": i + 1,
                    "tables": table_details
                })
        return stats
    
    def scan_single_page(pdf_path, page_index=0):
        """
        page_index: (0 is the first page)
        """
        with pdfplumber.open(pdf_path) as pdf:
            if page_index >= len(pdf.pages):
                print(f"Error: Page {page_index} out of range.")
                return

            page = pdf.pages[page_index]
            text = page.extract_text()

            # If text layer is missing or too short, use OCR
            if not text or len(text.strip()) < 10:
                print(f"Page {page_index + 1}: No text layeru using OCR")
                img = page.to_image(resolution=300).original
                # Get detailed data including confidence scores
                content = pytesseract.image_to_string(img, lang='eng')
            else:
                print(f"Page {page_index + 1}: Text layer detected.")
                content = text.strip()

            print(f"\n CONTENT START\n{content}\n CONTENT END ")
            return content
    

    def extract_formatted_well_data(pdf_path, page_index=0):
       
        data = {
            "file_no": None,
            "well_name": None,
            "location": None,
            "county": None,
            "is_ocr": False
        }

        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_index]
            text = page.extract_text()

            # 1. Check if we need OCR
            if not text or len(text.strip()) < 20:
                img = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(img, lang='eng')
                data["is_ocr"] = True
            
            # 2. Extract File Number 
            file_no_match = re.search(r'File No\.?\s*(\d+)', text, re.IGNORECASE)
            if file_no_match:
                data["file_no"] = file_no_match.group(1)

            # 3. Extract Well Name (Usually between 'Name and Number' and 'Qtr-Qtr')
            # We use a non-greedy catch-all to handle messy scanning
            well_name_match = re.search(r'Name and Number\s*(.*?)\s*Qtr-Qtr', text, re.S | re.I)
            if well_name_match:
                data["well_name"] = well_name_match.group(1).strip().replace('\n', ' ')

            # 4. Extract Location (PLSS format like SWSW 34-151-100)
            # Looking for common patterns in North Dakota forms
            loc_match = re.search(r'([NESW]{2}[NESW]{2})\s*(\d+)', text)
            if loc_match:
                data["location"] = f"{loc_match.group(1)} Section {loc_match.group(2)}"

            # 5. Extract County (Common ND counties)
            counties = ["McKenzie", "Williams", "Mountrail", "Dunn", "Billings"]
            for c in counties:
                if c.lower() in text.lower():
                    data["county"] = c
                    break

        return data
                    