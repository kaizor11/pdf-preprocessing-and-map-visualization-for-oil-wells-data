# pdf-preprocessing-and-map-visualization-for-oil-wells-data
This program extracts oil wells information from a list of 77 PDFs (each containing around 200 pages) using OCR and uses the extracted information (API#, latitude, longitude) to scrape additional information from a web database. AWS RDS MySQL database is used to store the extracted data. Finally, we visualize the oil wells data using OpenLayers.
<br>

**Initialization** <br>
- Download pytesseract, poppler (for pdf2image)
- `pip install -r requirements.txt`
- Create a `.env` file with your AWS RDS MySQL credentials (DB_USER, DB_PASSWORD) and change the server configs in `store_sql.py`
- In `pdf_extraction.py`, change `MAX_WORKERS` to the number of CPU cores in your device

**Execution** <br>
- Run PDF extraction `python pdf_extraction.py` --> `output.csv` (this process took around 33 minutes)
- Store data in MySQL `python store_sql.py`
- 