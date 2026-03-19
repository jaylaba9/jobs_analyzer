from collections import Counter
from datetime import date, timedelta, datetime
import os
import time
import requests
import random
import json
import streamlit as st
import pandas as pd
import plotly.express as px

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
        tuple: Tuple of postings(list), total pages (number) and current date
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
        current_date = date.today()
        response = session.post(url_post, headers=headers_post, params=params_post, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        print("POST request successful")
        full_data = response.json()
        total_pages = full_data.get("totalPages", 1) # default 1 page
        postings = full_data.get("postings", [])
        return postings, total_pages, current_date
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

def get_unique_offers() -> int:
    """
    Loads job offers from 'offers.json', removes duplicates (by company name and title),
    extracts URLs of unique offers, and saves them to 'urls.json'.

    Returns:
        int: number of unique offers
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

    return len(urls_list)

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

def analyze_technologies(filename: str) -> list:
    """
    Processes file that contains list of all scraped technologies, normalizes them and uses prepared map of synonyms to group them.
    Counts occurences of each technology and print top technologies with their counters. 

    Args:
        filename (str): name of the file that contains list of all scraped technologies

    Returns:
        counts.most_common(15) (list of tuples): Returns a list of tuples which contain technology and number of occurences, e.g. ('Linux', 50)
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

    return counts.most_common(15)


def visualize(offers: int, techs: list, current_date: date):
    st.title('Currently trending DevOps technologies')
    st.write(f'This application checked {offers} job offers from one of the IT job boards and retrieved must-have skills.')

    df = pd.DataFrame(techs, columns=['Technology', 'Occurences'])
    df = df.sort_values(by='Occurences', ascending=True)

    fig = px.bar(df, 
             x='Occurences', 
             y='Technology', 
             orientation='h', 
             title='Top 15 DevOps technologies',
             color='Occurences', 
             color_continuous_scale='Blues')

    st.plotly_chart(fig, use_container_width=True)

    st.write(f'This data was retrieved {current_date}. Next check will be done {current_date + timedelta(days=7)}')


@st.cache_data(show_spinner="Scraping data... This may take a few minutes.")
def get_or_fetch_data(tech_file, offers_file) -> tuple:
    """
    Orchestrates data retrieval by checking local cache freshness before scraping.

    This function implements a caching strategy: it first checks if the required 
    JSON files exist and if they are less than 7 days old. If the data is stale 
    or missing, it triggers the full scraping workflow (fetching listings, 
    processing unique URLs, and extracting technology details). Otherwise, 
    it loads existing data from the disk.

    Args:
        tech_file (str): Path to the JSON file containing aggregated technologies.
        offers_file (str): Path to the JSON file containing raw job postings.

    Returns:
        tuple: A tuple containing:
            - unique_offers (int): Total number of unique job offers processed.
            - most_common_techs (list): Top 15 technologies with their occurrence counts.
            - last_update_time (date): The date when the data was last synchronized.
    """
    should_update = False

    # 1. Check if files exist
    if not os.path.exists(tech_file) or not os.path.exists(offers_file):
        should_update = True
    else:
        # 2. Check mtime of file
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(tech_file))
        if datetime.now() > file_mod_time + timedelta(days=7):
            should_update = True

    if should_update:
        # --- SCRAPINg LOGIC ---
        # - Picks a random User-Agent.
        # - Starts a session and performs GET/POST requests.
        # - Saves job postings to 'offers.json' by looping over all available pages.
        # - Extracts and saves unique offer URLs to 'urls.json'.
        # - Fetches details of each offer (tech stack) and saves to 'technologies.json'.
        agent = random.choice(user_agents)
        session = get_session_and_cookies(url_get, agent)
        all_postings, total_pages, current_date = fetch_job_postings(session, agent, page=1)

        for current_page in range(2, total_pages + 1):
            new_postings, *_ = fetch_job_postings(session, agent, current_page)
            all_postings.extend(new_postings)
            time.sleep(1)
        if all_postings:
            save_to_file(data=all_postings, label="postings", filename=offers_file)

        unique_offers = get_unique_offers()
        fetch_offer_details(session, agent)
        print(f"Total offers: {unique_offers}")

    else:
        with open(offers_file, 'r', encoding='utf-8') as f:
            unique_offers = len(json.load(f))

    # get top15 technologies
    most_common_techs = analyze_technologies(filename=tech_file)

    last_update_time = datetime.fromtimestamp(os.path.getmtime(tech_file)).date()

    return unique_offers, most_common_techs, last_update_time


def main():
    """
    Entry point for the Streamlit application.
    
    Initializes file paths, invokes the data retrieval logic with built-in 
    caching, and passes the results to the visualization module. Handles 
    top-level exceptions to ensure a user-friendly error display.
    """
    tech_file = "technologies.json"
    offers_file = "offers.json"

    try:
        unique_offers, most_common_techs, update_date = get_or_fetch_data(tech_file, offers_file)

        visualize(unique_offers, most_common_techs, update_date)

    except Exception as e:
        st.error(f"An error occured during data processing: {e}")

if __name__ == "__main__":
    main()