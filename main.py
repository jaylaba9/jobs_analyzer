from collections import Counter
import time
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

def fetch_job_postings(session: requests.Session, agent: str, page: int = 1) -> tuple:
    """
    Sends a POST request to retrieve job postings from NoFluffJobs API.

    Args:
        session (requests.Session): Session object with cookies.
        agent (str): User-Agent string to include in the request header.
        page (int, optional): Page number to retrieve. Defaults to 1.

    Returns:
        tuple: Tuple of postings(list) and total pages (number)
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
        full_data = response.json()
        total_pages = full_data.get("totalPages", 1) # default 1 page
        postings = full_data.get("postings", [])
        return postings, total_pages
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

def fetch_offer_details(session: requests.Session, agent: str) -> None:
    """
    Loads SLUGs of job postings from the urls.json file. Then, fetches "must-have" technologies by sending a GET request to each of the postings using base API URL + SLUG. Saves result in a file.

    Args:
        session (requests.Session): Session object with cookies.
        agent (str): User-Agent string to include in the request header.

    Returns:
        None
    """
    with open("urls.json", "r", encoding='utf-8') as f:
        urls = json.load(f)

    headers = {
        "User-Agent": agent,
        "Accept": "application/json, text/plain, */*"
    }

    api_url = "https://nofluffjobs.com/api/posting/"

    result = []
    for url in urls:
        try:
            current_url = api_url + url
            response = session.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            full_data = response.json()
            # list comprehension to retrieve only names of technologies - field value. This data looks like this:
            # "requirements": {
            #   "musts": [
            #       {
            #       "value": "SRE",
            #       "type": "main"
            # },
            musts = [req['value'] for req in full_data.get('requirements', {}).get('musts', [])]
            result.extend(musts)
            print(f"Fetched: {url}")
            time.sleep(random.randint(1,3))
        except Exception as e:
            print(f"Error while fetching data from {url}: {e}")

    if result:
        save_to_file(data=result, label='technologies', filename='technologies.json')

# synonyms map prepared to group technologies from 'technologies.json'
synonyms_map = {
    # Cloud
    "aws": "AWS",
    "amazon web services": "AWS",
    "amazon eks": "Kubernetes",
    "eks": "Kubernetes",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "azure cloud": "Azure",
    "aks": "Kubernetes",
    "azure kubernetes service": "Kubernetes",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "gke": "Kubernetes",
    "oci": "Oracle Cloud",

    # Containerization and Orchestration
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "docker compose": "Docker",
    "helm": "Helm",
    "helm charts": "Helm",
    "openshift": "OpenShift",

    # Infrastructure as Code (IaC)
    "iac": "Infrastructure as Code",
    "infrastructure as code": "Infrastructure as Code",
    "infrastructure as a code": "Infrastructure as Code",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "cloudformation": "CloudFormation",
    "aws cloudformation": "CloudFormation",
    "bicep": "Bicep",
    "pulumi": "Pulumi",

    # CI/CD
    "ci/cd": "CI/CD",
    "ci cd": "CI/CD",
    "ci/cd pipelines": "CI/CD",
    "ci cd pipelines": "CI/CD",
    "github actions": "GitHub Actions",
    "jenkins": "Jenkins",
    "gitlab ci": "GitLab CI",
    "gitlab ci/cd": "GitLab CI",
    "argocd": "ArgoCD",
    "argo cd": "ArgoCD",

    # Programming and scripting
    "python": "Python",
    "golang": "Go",
    "go": "Go",
    "bash": "Bash",
    "shell": "Bash",
    "bash script": "Bash",
    "powershell": "PowerShell",
    "groovy": "Groovy",

    # Monitorings and logs
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "elk stack": "ELK Stack",
    "elk": "ELK Stack",
    "kibana": "ELK Stack",
    "splunk": "Splunk",
    "datadog": "Datadog",

    # Network and others
    "networking": "Networking",
    "network protocols": "Networking",
    "security": "Security",
    "cybersecurity": "Security",
    "git": "Git",
    "version control system": "Git"
}

def analyze_technologies(filename: str) -> None:
    """
    Processes file that contains list of all scraped technologies, normalizes them and uses prepared map of synonyms to group them.
    Counts occurences of each technology and print top technologies with their counters. 

    Args:
        filename (str): name of the file that contains list of all scraped technologies

    Returns:
        None
    """
    with open(filename, 'r', encoding='utf-8') as f:
        raw_techs = json.load(f)

    clean_list = []
    for tech in raw_techs:
        # Normalize (lower case and space removal)
        name = tech.lower().strip()

        # Synonyms mapping
        # If name is not in map, original one is kept
        standardized_name = synonyms_map.get(name, tech)

        clean_list.append(standardized_name)

    # Counting
    counts = Counter(clean_list)

    # Printing top15
    print(f"{'Technology':<25} | {'Occurences':<10}")
    print('-' * 40)
    for tech, count in counts.most_common(15):
        print(f"{tech:<25} | {count:<10}")

def main():
    """
    Main execution flow:
    - Picks a random User-Agent.
    - Starts a session and performs GET/POST requests.
    - Saves job postings to 'offers.json' by looping over all available pages.
    - Extracts and saves unique offer URLs to 'urls.json'.
    - Fetches details of each offer (tech stack) and saves to 'technologies.json'.
    """
    agent = random.choice(user_agents)
    session = get_session_and_cookies(url_get, agent)
    all_postings, total_pages = fetch_job_postings(session, agent, page=1)

    for current_page in range(2, total_pages + 1):
        new_postings, _ = fetch_job_postings(session, agent, current_page)
        all_postings.extend(new_postings)
        time.sleep(1)
    if all_postings:
        save_to_file(data=all_postings, label="postings", filename="offers.json")

    get_unique_offers()
    fetch_offer_details(session, agent)
    analyze_technologies(filename="technologies.json")

if __name__ == "__main__":
    main()