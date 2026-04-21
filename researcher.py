import requests
from bs4 import BeautifulSoup
import time

def search_company_website(company_name):
    """
    Searches for a company's website and scrapes its 'About Us' page.

    Args:
        company_name (str): The name of the company to research.

    Returns:
        str: The text content of the company's 'About Us' page, or a summary from the homepage.
             Returns None if the website cannot be found or scraped.
    """
    print(f"Researching {company_name}...")
    try:
        # Using DuckDuckGo's HTML search to avoid needing an API key for simple searches
        search_url = f"https://html.duckduckgo.com/html/?q={company_name} official website"
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36'}
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first search result link
        result_links = soup.find_all('a', class_='result__a')
        if not result_links:
            print(f"No search results found for {company_name}.")
            return None
            
        first_link = result_links[0]['href']
        
        # DuckDuckGo links are redirect URLs, so we need to clean them
        from urllib.parse import unquote, urlparse, parse_qs
        
        # The actual URL is in the 'uddg' query parameter
        parsed_link = urlparse(first_link)
        actual_url = parse_qs(parsed_link.query).get('uddg', [None])[0]

        if not actual_url:
            print(f"Could not extract a valid URL for {company_name}.")
            return None

        actual_url = unquote(actual_url)

        print(f"Found website for {company_name}: {actual_url}")

        # Now, let's try to find an 'About Us' page
        # This is a simple guess, more sophisticated logic could be added
        about_url = f"{actual_url.strip('/')}/about"
        
        response = requests.get(about_url, headers=headers, timeout=10)
        if response.status_code == 200:
            page_content = response.text
            print(f"Found 'About Us' page for {company_name}.")
        else:
            # If no about page, just use the homepage
            response = requests.get(actual_url, headers=headers, timeout=10)
            response.raise_for_status()
            page_content = response.text
            print(f"Using homepage for {company_name}.")

        soup = BeautifulSoup(page_content, 'html.parser')
        # Get all the text from the page
        text = soup.get_text(separator=' ', strip=True)
        
        # Let's return a summary (e.g., first 1000 characters)
        return text[:1000]

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during web request for {company_name}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while researching {company_name}: {e}")
        return None
    finally:
        # To be a good web citizen, let's add a small delay between requests
        time.sleep(2)


if __name__ == '__main__':
    # This is for testing purposes.
    company_name = "Microsoft"  # Example company
    about_text = search_company_website(company_name)
    if about_text:
        print(f"\nResearch summary for {company_name}:\n")
        print(about_text)
