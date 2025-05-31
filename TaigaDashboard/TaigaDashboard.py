from flask import Flask, render_template
from app.taiga_factory import create_taiga_client
import json

app = Flask(__name__)


@app.route("/")
def home():
    client = create_taiga_client()
    epics = client.get_epics()
    epics_json = json.dumps(epics, indent=2)
    userstories = client.get_stories()
    userstories_json = json.dumps(userstories, indent=2)
    tasks = client.get_tasks()
    tasks_json = json.dumps(tasks, indent=2)
    issues = client.get_issues()
    issues_json = json.dumps(issues, indent=2)
    return render_template("index.html", epics_json=epics_json, userstories_json=userstories_json, tasks_json=tasks_json, issues_json=issues_json)


if __name__ == "__main__":
    app.run(debug=True)