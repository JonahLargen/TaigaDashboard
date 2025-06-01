import requests


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
        response = self.session.post(url, json=json_payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        self.auth_token = data.get("auth_token")

        print(f"Auth Token: {self.auth_token}") 

        if not self.auth_token:
            raise ValueError("Authentication failed. Please check your credentials.")

        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        self.is_authenticated = True

    def ensure_authenticated(self):
        """Ensure the user is authenticated."""
        if not self.is_authenticated:
            self.authenticate()

    def get_epics(self):
        """
        Retrieve all epics for the configured project.
        Returns: List of epic dicts.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/epics?project={self.projectid}"
        print(f"Fetching epics from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_stories(self):
        """
        Retrieve all stories for the configured project.
        Returns: List of story dicts.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/userstories?project={self.projectid}"
        print(f"Fetching user stories from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_tasks(self):
        """
        Retrieve all tasks for the configured project.
        Returns: List of task dicts.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/tasks?project={self.projectid}"
        print(f"Fetching tasks from: {url}")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_issues(self):
        """
        Retrieve all issues for the configured project.
        Returns: List of issue dicts.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/issues?project={self.projectid}"
        print(f"Fetching issues from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_sprints(self):
        """
        Retrieve all sprints/milestones for the configured project.
        Returns: List of issue dicts.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/milestones?project={self.projectid}"
        print(f"Fetching sprints from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_project(self):
        """
        Retrieve the project information.
        Returns: Project details.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/projects/{self.projectid}"
        print(f"Fetching project from: {url}")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_users(self):
        """
        Retrieve the project users.
        Returns: User details.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/users?project={self.projectid}"
        print(f"Fetching users from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_users(self):
        """
        Retrieve the project users.
        Returns: User details.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/users?project={self.projectid}"
        print(f"Fetching users from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_issue_types(self):
        """
        Retrieve the project issue types.
        Returns: Issue Types details.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/issue-types?project={self.projectid}"
        print(f"Fetching issue types from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_severities(self):
        """
        Retrieve the project issue severities.
        Returns: Severity details.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/severities?project={self.projectid}"
        print(f"Fetching severities from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_priorities(self):
        """
        Retrieve the project issue priorities.
        Returns: Priority details.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/api/v1/priorities?project={self.projectid}"
        print(f"Fetching priorities from: {url}") 
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()