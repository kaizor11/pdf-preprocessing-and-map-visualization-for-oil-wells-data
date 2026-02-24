import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from urllib.parse import urljoin, quote
import time

# Constant header used across all network requests to simulate a real browser
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def read_inputs_from_csv(filepath):
    df = pd.read_csv(filepath)
    records = []
    
    for index, row in df.iterrows():
        # Skip rows where file_num is empty (NaN)
        if pd.isna(row['file_num']):
            continue
            
        # Convert float (11745.0) to integer (11745) then to string
        api_no = str((row['api']))
        well_name = str(row['well_name'])
        operator  = str(row['operator'])
        records.append({
            'api_no': api_no,
            'well_name': well_name,
            'operator' : operator,
        })
        
    return records

def get_detail_url(api_no="", operator_name="", well_name=""):
   
    # quote() ensures that spaces and special characters are safely URL-encoded
    safe_api = quote(str(api_no))
    safe_operator = quote(str(operator_name))
    safe_well = quote(str(well_name))
    
    # f-string format with placeholders for the keywords
    search_url = f"https://www.drillingedge.com/search?type=wells&operator_name={safe_operator}&well_name={safe_well}&api_no={safe_api}&lease_key=&state=&county=&section=&township=&range=&min_boe=&max_boe=&min_depth=&max_depth=&field_formation="
    
    try:
        res = requests.get(search_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Look for the first link containing '/wells/'
        link_tag = soup.find('a', href=re.compile(r'/wells/'))
        if not link_tag:
            return None
            
        return urljoin("https://www.drillingedge.com", link_tag['href'])
        
    except Exception as e:
        print(f"  Error finding detail URL: {e}")
        return None

def scrape_detail_page(detail_url, api_no, well_name):
    try:
        res = requests.get(detail_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        def get_val(label_pattern):
           
            elem = soup.find(string=re.compile(label_pattern, re.IGNORECASE))
            if elem and elem.find_next('td'):
                val = elem.find_next('td').text.strip()
                return val if val else "N/A"
            return "N/A"

       
     

       
        return {
            'API_Number': api_no,
            'Well_Name': well_name,
            'Status': get_val(r'Status'),
            'Type': get_val(r'Type'),
            'Closest_City': get_val(r'Closest City'),
            'First_Production_Date': get_val(r'First Production Date on File'),
            'Most_Recent_Production_Date': get_val(r'Most Recent Production Date on File'),
            'Latitude_Longitude': get_val(r'Latitude\s*/\s*Longitude'),
         
        }
        
    except Exception as e:
        print(f"  Error scraping detail page: {e}")
        return None
def get_drillingedge_well_links(page_url):
   
  
    try:
        res = requests.get(page_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Regex pattern
        # drillingedge\.com : Matches the domain name literally 
        # .*?               : Matches the state and county parts non-greedily
        # /wells/           : Matches the specific wells subfolder
        pattern = re.compile(r'drillingedge\.com/.*?/wells/', re.IGNORECASE)
        
        # Find all <a> tags with an href matching the pattern
        link_tags = soup.find_all('a', href=pattern)
        
        # Extract the 'href' attribute and remove duplicates
        unique_links = []
        for tag in link_tags:
            href = tag['href']
            if href not in unique_links:
                unique_links.append(href)
                
        return unique_links
        
    except Exception as e:
        print(f"Failed to get links from {page_url}: {e}")
        return []

def main():
    """
    Main controller function that combines the workflow.
    """
    input_csv = "output.csv"
    output_csv = "scraped_data.csv"
    
    print("Reading targets from CSV...")
    targets = read_inputs_from_csv(input_csv)
    print(f"Found {len(targets)} valid targets to scrape.\n")
    
    all_results = []
    
    for target in targets:
        api_no = target['api_no']
        well_name = target['well_name']
        
        print(f"Processing API: {api_no} ({well_name})")
        
        # Get the detail URL
        detail_url = get_detail_url(api_no)
        if not detail_url:
            print(f"  -> Search failed. No link found.")
            continue
            
        print(f"  -> Found link: {detail_url}")
        
        
        time.sleep(1)
        
        # Scrape the detail page
        data = scrape_detail_page(detail_url, api_no, well_name)
        if data:
            all_results.append(data)
            print("  -> Data extracted successfully.")
            
    # Export results
    if all_results:
        df_out = pd.DataFrame(all_results)
        df_out.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\nWorkflow complete. Saved {len(all_results)} rows to {output_csv}")
    else:
        print("\nWorkflow complete. No data was extracted.")

if __name__ == "__main__":
    main()