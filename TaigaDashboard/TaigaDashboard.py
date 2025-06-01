from flask import Flask, render_template
from app.taiga_factory import create_taiga_client
from app.taiga_plotly import (
    get_epic_progress_html,
    get_task_status_breakdown_html,
    get_task_assignment_heatmap_html,
)
from dotenv import load_dotenv
import json

app = Flask(__name__)

load_dotenv()  # loads .env file into environment variables


@app.route("/")
def home():
    client = create_taiga_client()
    epics = client.get_epics()
    userstories = client.get_stories()
    tasks = client.get_tasks()
    issues = client.get_issues()
    sprints = client.get_sprints()
    project = client.get_project()
    users = client.get_users()

    epics_json = json.dumps(epics, indent=2)
    userstories_json = json.dumps(userstories, indent=2)
    tasks_json = json.dumps(tasks, indent=2)
    issues_json = json.dumps(issues, indent=2)
    sprints_json = json.dumps(sprints, indent=2)
    project_json = json.dumps(project, indent=2)
    users_json = json.dumps(users, indent=2)

    project_name = project["name"]
    epic_progress_bar_html = get_epic_progress_html(epics, userstories)
    user_story_status_breakdown_html = get_task_status_breakdown_html(
        userstories, [], [], sprints, "User Story Status Breakdown by Sprint"
    )
    task_status_breakdown_html = get_task_status_breakdown_html(
        [], tasks, issues, sprints, "Work Item (Task/Issue) Status Breakdown by Sprint"
    )
    task_assignment_heatmap_html = get_task_assignment_heatmap_html(
        users, userstories, tasks, issues
    )

    return render_template(
        "index.html",
        project_name=project_name,
        epic_progress_bar_html=epic_progress_bar_html,
        user_story_status_breakdown_html=user_story_status_breakdown_html,
        task_status_breakdown_html=task_status_breakdown_html,
        task_assignment_heatmap_html=task_assignment_heatmap_html,
        epics_json=epics_json,
        userstories_json=userstories_json,
        tasks_json=tasks_json,
        issues_json=issues_json,
        sprints_json=sprints_json,
        project_json=project_json,
        users_json=users_json,
    )


if __name__ == "__main__":
    app.run(debug=True)