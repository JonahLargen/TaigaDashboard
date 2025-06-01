from flask import Flask, render_template
from app.taiga_factory import create_taiga_client
from app.taiga_plotly import (
    get_dashboard_config_html,
    get_epic_progress_html,
    get_task_status_breakdown_html,
    get_task_assignment_heatmap_html,
    get_task_createdby_heatmap_html,
    get_tag_cloud_html,
    get_tag_bar_chart_html,
    get_issue_type_severity_priority_donut_charts_html,
    get_blocked_items_table_html
)
from dotenv import load_dotenv
import json
from flask_caching import Cache

app = Flask(__name__)

load_dotenv()  # loads .env file into environment variables

cache = Cache(config={"CACHE_TYPE": "simple"})
cache.init_app(app)


@app.route("/")
@cache.cached(timeout=900)  # 900 seconds = 15 minutes
def home():
    client = create_taiga_client()
    epics = client.get_epics()
    userstories = client.get_stories()
    tasks = client.get_tasks()
    issues = client.get_issues()
    sprints = client.get_sprints()
    project = client.get_project()
    users = client.get_users()
    severities = client.get_severities()
    priorities = client.get_priorities()
    issue_types = client.get_issue_types()

    project_name = project["name"]
    project_id = project["id"]
    logo = project["logo_small_url"]
    dashboard_config_html = get_dashboard_config_html()
    epic_progress_bar_html = get_epic_progress_html(epics, userstories)
    user_story_status_breakdown_html = get_task_status_breakdown_html(
        userstories,
        [],
        [],
        sprints,
        "User Story Status Breakdown by Sprint (Requirement Items)",
    )
    task_status_breakdown_html = get_task_status_breakdown_html(
        [], tasks, issues, sprints, "Task/Issue Status Breakdown by Sprint (Work Items)"
    )
    task_assignment_heatmap_html = get_task_assignment_heatmap_html(
        users, userstories, tasks, issues
    )
    task_createdby_heatmap_html = get_task_createdby_heatmap_html(
        users, userstories, tasks, issues
    )
    tag_cloud_html = get_tag_cloud_html(userstories, tasks, issues)
    tag_bar_chart_html = get_tag_bar_chart_html(userstories, tasks, issues)
    issue_type_severity_priority_donut_charts_html = (
        get_issue_type_severity_priority_donut_charts_html(
            issues, issue_types, severities, priorities
        )
    )
    blocked_items_table_html = get_blocked_items_table_html(epics, userstories, tasks, issues)

    return render_template(
        "index.html",
        project_name=f"{project_name} ({project_id})",
        logo=logo,
        dashboard_config_html=dashboard_config_html,
        epic_progress_bar_html=epic_progress_bar_html,
        user_story_status_breakdown_html=user_story_status_breakdown_html,
        task_status_breakdown_html=task_status_breakdown_html,
        task_assignment_heatmap_html=task_assignment_heatmap_html,
        task_createdby_heatmap_html=task_createdby_heatmap_html,
        tag_cloud_html=tag_cloud_html,
        tag_bar_chart_html=tag_bar_chart_html,
        issue_type_severity_priority_donut_charts_html=issue_type_severity_priority_donut_charts_html,
        blocked_items_table_html=blocked_items_table_html
    )


if __name__ == "__main__":
    app.run(debug=True)