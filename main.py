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

# GET to catch cookies and store them in session object
def get_session_and_cookies(url_get: str, agent: str) -> requests.Session:
    # Start a HTTP session
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

# POST to retrieve job postings data as a list
def fetch_job_postings(session: requests.Session, agent: str, page: int = 1) -> list:
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
    
def save_to_file(data: list, object: str, filename: str):
    try:
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} {object} to {filename}")
    except Exception as e:
        print(f"Failed to save file {filename}: {e}")

def main():
    # Randomly choosing one of the user_agents that will be used during the session (both POST and GET)
    agent = random.choice(user_agents)
    session = get_session_and_cookies(url_get, agent)
    postings = fetch_job_postings(session, agent, page=4)
    if postings:
        save_to_file(data=postings, object="postings", filename="offers.json")
    
if __name__ == "__main__":
    main()