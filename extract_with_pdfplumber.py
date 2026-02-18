import os
import pdfplumber
from pathlib import Path


class  plumber_processor:

    # initializing the class 
    def __init__(self,folder = "./data"):
        # ./data is the path of pdf

        self.folder = Path(folder)
    
    def GetPdfNames(self,prefix ="W"):
        


        folder = self.folder
        print(f"using prefix {prefix}")
        pdf_files = folder.glob(f"{prefix}*.pdf")
        print()
       
        

        try:
           
            sorted_files = sorted(pdf_files, key=lambda p: int(p.stem[len(prefix):]))
        except ValueError as e:
            print("formattign error!")
            return []
        
        for f in sorted_files[:10]:
            print(f.name)

        return sorted_files