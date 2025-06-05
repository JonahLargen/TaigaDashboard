import requests
import time
from datetime import datetime

class TaigaClient:
    def __init__(self, base_url, username, password, projectid):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.projectid = projectid
        self.auth_token = None
        self.is_authenticated = False

    def authenticate(self):
        """Authenticate the user and store the session cookie."""
        url = f"{self.base_url}/api/v1/auth"
        json_payload = {
            "username": self.username,
            "password": self.password,
            "type": "normal",
        }
        headers = {"Content-Type": "application/json"}
        start_time = time.perf_counter()
        response = self.session.post(url, json=json_payload, headers=headers)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] POST {url} took {duration:.3f} seconds")
        response.raise_for_status()
        data = response.json()

        self.auth_token = data.get("auth_token")

        if not self.auth_token:
            raise ValueError("Authentication failed. Please check your credentials.")

        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        self.is_authenticated = True

    def ensure_authenticated(self):
        """Ensure the user is authenticated."""
        if not self.is_authenticated:
            self.authenticate()

    def _paginated_get(self, endpoint, params=None):
        """
        Fetch all items from a paginated Taiga endpoint using pagination headers.
        Logs the time for each request.
        """
        params = params or {}
        url = f"{self.base_url}{endpoint}"
        all_items = []
        page_num = 1

        while url:
            start_time = time.perf_counter()
            response = self.session.get(url, params=params if '?' not in url else None)
            duration = time.perf_counter() - start_time
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] GET {url} (page {page_num}) took {duration:.3f} seconds")
            response.raise_for_status()
            items = response.json()
            if isinstance(items, list):
                all_items.extend(items)
            elif isinstance(items, dict) and "results" in items:
                all_items.extend(items["results"])
            else:
                all_items.extend(items)
            next_url = response.headers.get("x-pagination-next")
            if next_url:
                url = next_url if next_url.startswith("http") else f"{self.base_url}{next_url}"
                params = None
                page_num += 1
            else:
                break
        return all_items

    def get_epics(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/epics"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all epics from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_epics completed in {duration:.3f} seconds")
        return result

    def get_stories(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/userstories"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all user stories from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_stories completed in {duration:.3f} seconds")
        return result

    def get_tasks(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/tasks"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all tasks from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_tasks completed in {duration:.3f} seconds")
        return result

    def get_issues(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/issues"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all issues from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_issues completed in {duration:.3f} seconds")
        return result

    def get_sprints(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/milestones"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all sprints from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_sprints completed in {duration:.3f} seconds")
        return result

    def get_project(self):
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/projects/{self.projectid}"
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching project from: {url}")
        start_time = time.perf_counter()
        response = self.session.get(url)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] GET {url} took {duration:.3f} seconds")
        response.raise_for_status()
        return response.json()

    def get_users(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/users"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all users from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_users completed in {duration:.3f} seconds")
        return result

    def get_issue_types(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/issue-types"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all issue types from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_issue_types completed in {duration:.3f} seconds")
        return result

    def get_severities(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/severities"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all severities from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_severities completed in {duration:.3f} seconds")
        return result

    def get_priorities(self):
        self.ensure_authenticated()
        endpoint = "/api/v1/priorities"
        params = {"project": self.projectid}
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Fetching all priorities from: {self.base_url}{endpoint} with params: {params}")
        start_time = time.perf_counter()
        result = self._paginated_get(endpoint, params)
        duration = time.perf_counter() - start_time
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] get_priorities completed in {duration:.3f} seconds")
        return result