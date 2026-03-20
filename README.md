# DevOps Job Market Analyzer

Interactive dashboard built with **Python**, **Streamlit**, and **Docker** that scrapes, processes, and visualizes the most in-demand technologies in the DevOps landscape based on real-time data from one of the IT job boards.
Preview:
<img width="1902" height="868" alt="image" src="https://github.com/user-attachments/assets/7a69689e-8ecf-4873-872a-e1a7fdca9b66" />


---

### Key Features
* **Automated Scraping:** Periodically fetches job postings from IT job board API.
* **Smart Caching:** Uses st.cache_data and file-system checks to prevent redundant scraping (scans once every 7 days).
* **Data Normalization:** Maps technology synonyms (e.g., "K8s", "Amazon EKS" -> "Kubernetes") for accurate counting.
* **Interactive Visualization:** Horizontal bar charts showing the Top 15 "Must-Have" skills.
* **Containerized Environment:** Fully dockerized.

### Tech Stack
* **Language:** Python
* **Framework:** [Streamlit](https://streamlit.io/)
* **Data Analysis:** Pandas, Collections
* **Visualization:** Plotly Express
* **DevOps:** Docker

---

### Getting Started

#### Prerequisites
* Docker installed on your machine.
* (Optional) Python 3.13 for local execution without Docker.

#### Running with Docker (Recommended)
To keep your data persistent use Docker Volumes. 

1.  **Build the image:**
    ```bash
    docker build -t devops-analyzer .
    ```

2.  **Run the container:**

    **If using Git Bash (Windows):**
    ```bash
    docker run -d -p 8501:8501 -v "/$(pwd)://app" devops-analyzer
    ```

    **If using Linux/macOS:**
    ```bash
    docker run -d -p 8501:8501 -v "$(pwd):/app" devops-analyzer
    ```

    **If using Windows CMD:**
    ```cmd
    docker run -d -p 8501:8501 -v "%cd%:/app" devops-analyzer
    ```

3.  **Access the Dashboard:**
    Open your browser and go to: [http://localhost:8501](http://localhost:8501)

---

### How it works
1.  **Initialization:** Upon startup, the app checks if `technologies.json` exists and is fresh (less than 7 days old).
2.  **Scraping Phase:** If data is stale or missing, the script performs a series of GET/POST requests to fetch the latest DevOps job offers.
3.  **Processing:** It extracts "must-have" requirements, standardizes names using a predefined synonym map, and counts occurrences.
4.  **Display:** Streamlit renders a responsive dashboard with the latest market insights.
