from flask import Flask, render_template
from app.taiga_factory import create_taiga_client
from app.taiga_plotly import get_epic_progress_html
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

    print(epics)
    print(userstories)

    epics_json = json.dumps(epics, indent=2)
    userstories_json = json.dumps(userstories, indent=2)
    tasks_json = json.dumps(tasks, indent=2)
    issues_json = json.dumps(issues, indent=2)

    epic_progress_bar_html = get_epic_progress_html(epics, userstories)

    return render_template(
        "index.html",
        epic_progress_bar_html=epic_progress_bar_html,
        epics_json=epics_json,
        userstories_json=userstories_json,
        tasks_json=tasks_json,
        issues_json=issues_json,
    )


if __name__ == "__main__":
    app.run(debug=True)