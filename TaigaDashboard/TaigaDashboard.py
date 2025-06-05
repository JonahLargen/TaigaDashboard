from flask import Flask, render_template, request, abort
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
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

load_dotenv()  # loads .env file into environment variables

API_KEY = os.environ.get("API_KEY")

cache = Cache(config={"CACHE_TYPE": "simple"})
cache.init_app(app)


@app.route("/")
@cache.cached(timeout=900)  # 900 seconds = 15 minutes
def home():
    if API_KEY:
        req_key = request.args.get("key")
        if not req_key or req_key != API_KEY:
            abort(403)  # Forbidden

    client = create_taiga_client()

    start_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    overall_start = time.perf_counter()
    print(f"[{start_timestamp}] Starting full Taiga data fetch...")

    all_data = fetch_all_parallel(client)
    epics = all_data["epics"]
    userstories = all_data["userstories"]
    tasks = all_data["tasks"]
    issues = all_data["issues"]
    sprints = all_data["sprints"]
    project = all_data["project"]
    users = all_data["users"]
    severities = all_data["severities"]
    priorities = all_data["priorities"]
    issue_types = all_data["issue_types"]

    end_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    overall_duration = time.perf_counter() - overall_start
    print(f"[{end_timestamp}] Finished full Taiga data fetch in {overall_duration:.3f} seconds")

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

def fetch_all_parallel(client):
    tasks = {
        "epics": lambda: client.get_epics(),
        "userstories": lambda: client.get_stories(),
        "tasks": lambda: client.get_tasks(),
        "issues": lambda: client.get_issues(),
        "sprints": lambda: client.get_sprints(),
        "project": lambda: client.get_project(),
        "users": lambda: client.get_users(),
        "severities": lambda: client.get_severities(),
        "priorities": lambda: client.get_priorities(),
        "issue_types": lambda: client.get_issue_types(),
    }
    results = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_name = {executor.submit(func): name for name, func in tasks.items()}
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                print(f"{name} generated an exception: {exc}")
                results[name] = None
    return results


if __name__ == "__main__":
    app.run(debug=True)