import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin  
def scrape_drillingedge_exact(api_no):
    search_url = f"https://www.drillingedge.com/search?type=wells&operator_name=&well_name=&api_no={api_no}&lease_key=&state=&county=&section=&township=&range=&min_boe=&max_boe=&min_depth=&max_depth=&field_formation="
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print(f"Searching for API: {api_no}...")
    
    try:
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        link_tag = soup.find('a', href=re.compile(r'/wells/'))
        if not link_tag:
            print("No well found in search results.")
            return None
            
       
        detail_url = urljoin("https://www.drillingedge.com", link_tag['href'])
        print(f"Found detail page: {detail_url}")
        
        detail_res = requests.get(detail_url, headers=headers)
        detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
        
        def get_val(label):
            elem = detail_soup.find(string=re.compile(label, re.IGNORECASE))
            if elem and elem.find_next('td'):
                return elem.find_next('td').text.strip()
            return "N/A"

        data = {
            'API_Number': api_no,
            'Status': get_val('Status'),
            'Type': get_val('Type'),
            'Closest_City': get_val('Closest City'),
            'Oil_Produced': get_val('Oil Produced'),
            'Gas_Produced': get_val('Gas Produced')
        }
        
        return data

    except Exception as e:
        print(f"Error occurred: {e}")
        return None


if __name__ == "__main__":
    result = scrape_drillingedge_exact("33-053-06057")
    
    print("\n--- Extracted Data ---")
    if result:  
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("Scraping failed or no data returned.")