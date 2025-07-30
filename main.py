import requests
import random
import json

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"
]

url_get = "https://nofluffjobs.com/pl/devops"
url_post = "https://nofluffjobs.com/api/search/posting"

def get_session_and_cookies(url_get: str, agent: str) -> requests.Session:
    """
    Initiates an HTTP session and sends a GET request to retrieve cookies.

    Args:
        url_get (str): The URL to send the GET request to.
        agent (str): User-Agent string to mimic browser behavior.

    Returns:
        requests.Session: A session object with stored cookies.
    """
    session = requests.Session() 
    headers_get = {
        "User-Agent": agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    try:
        resp = session.get(url_get, headers=headers_get, timeout=10) # resp variable won't be used, it only matters that session.get() was executed
        resp.raise_for_status()
        print("GET request successful")
    except requests.exceptions.RequestException as e:
        print(f"Error while GET request: {e}")
        exit(1)
    return session

def fetch_job_postings(session: requests.Session, agent: str, page: int = 1) -> list:
    """
    Sends a POST request to retrieve job postings from NoFluffJobs API.

    Args:
        session (requests.Session): Session object with cookies.
        agent (str): User-Agent string to include in the request header.
        page (int, optional): Page number to retrieve. Defaults to 1.

    Returns:
        list: A list of job postings dictionaries.
    """
    headers_post = {
        "User-Agent": agent,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/infiniteSearch+json",
        "Origin": "https://nofluffjobs.com",
        "Referer": "https://nofluffjobs.com/pl/devops"
    }

    params_post = {
        "withSalaryMatch": "true",
        "pageTo": page,
        "pageSize": 20,
        "salaryCurrency": "PLN",
        "salaryPeriod": "month",
        "region": "pl",
        "language": "pl-PL",
    }

    payload = {
        "url": {"searchParam": "devops"},
        "rawSearch": "devops",
        "pageSize": 20,
        "withSalaryMatch": True,
        "page": page
    }

    try:
        response = session.post(url_post, headers=headers_post, params=params_post, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        print("POST request successful")
        return response.json().get("postings", [])
    except requests.exceptions.RequestException as e:
        print(f"Error while POST request: {e}")
        return []
    
def save_to_file(data: list, label: str, filename: str) -> None:
    """
    Saves the given data to a JSON file.

    Args:
        data (list): List of data to save.
        label (str): Label used for print messages (e.g., 'postings', 'urls').
        filename (str): Name of the output JSON file.

    Returns:
        None
    """
    try:
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} {label} to {filename}")
    except Exception as e:
        print(f"Failed to save file {filename}: {e}")

def get_posting_url(places: list):
    """
    Extracts the URL of the job posting from the list of places.

    Args:
        places (list): List of location dictionaries from a job offer.

    Returns:
        str or None: URL string if available, otherwise None.
    """
    if places:
        return places[0]["url"] # only first URL is enough, as offers may have many urls depending on number of available locations
    return None

def get_unique_offers() -> None:
    """
    Loads job offers from 'offers.json', removes duplicates (by company name and title),
    extracts URLs of unique offers, and saves them to 'urls.json'.

    Returns:
        None
    """
    with open("offers.json", "r", encoding='utf-8') as f:
        offers = json.load(f)

    unique_offers = {}
    for offer in offers:
        key = (offer["name"], offer["title"]) # a tuple of company name and a title, e.g. ("Google", "Senior Cloud Engineer")
        if key not in unique_offers:
            url = get_posting_url(offer["location"]["places"])
            if url:
                unique_offers[key] = url

    urls_list = list(unique_offers.values())
    save_to_file(data=urls_list, label='urls', filename="urls.json")

def main():
    """
    Main execution flow:
    - Picks a random User-Agent.
    - Starts a session and performs GET/POST requests.
    - Saves job postings to 'offers.json'.
    - Extracts and saves unique offer URLs to 'urls.json'.
    """
    agent = random.choice(user_agents)
    session = get_session_and_cookies(url_get, agent)
    postings = fetch_job_postings(session, agent, page=4)
    if postings:
        save_to_file(data=postings, label="postings", filename="offers.json")

    get_unique_offers()
    
if __name__ == "__main__":
    main()