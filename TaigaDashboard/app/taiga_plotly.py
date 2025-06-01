import plotly.graph_objs as go
import plotly
import os
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd


def get_int_from_env(var_name, default=0):
    """Read an integer value from env, or return default."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_statuses_from_env(var_name, default=None):
    """Read a comma-separated status list from env, return as a set of lowercased strings."""
    value = os.getenv(var_name)
    if value is None:
        return set(default or [])
    return set(v.strip().lower() for v in value.split(",") if v.strip())


EPIC_DAYS_AFTER_CLOSE = get_int_from_env("EPIC_DAYS_AFTER_CLOSE", 14)
USER_STORY_DAYS_AFTER_CLOSE = get_int_from_env("USER_STORY_DAYS_AFTER_CLOSE", 14)
TASK_DAYS_AFTER_CLOSE = get_int_from_env("TASK_DAYS_AFTER_CLOSE", 14)
ISSUE_DAYS_AFTER_CLOSE = get_int_from_env("ISSUE_DAYS_AFTER_CLOSE", 14)

USER_STORY_DONE_STATUSES = get_statuses_from_env("USER_STORY_DONE_STATUSES", ["done"])
USER_STORY_IN_PROGRESS_STATUSES = get_statuses_from_env(
    "USER_STORY_IN_PROGRESS_STATUSES", ["in progress"]
)
USER_STORY_NEW_STATUSES = get_statuses_from_env("USER_STORY_NEW_STATUSES", ["new"])

TASK_DONE_STATUSES = get_statuses_from_env("TASK_DONE_STATUSES", ["done"])
TASK_IN_PROGRESS_STATUSES = get_statuses_from_env(
    "TASK_IN_PROGRESS_STATUSES", ["in progress"]
)
TASK_NEW_STATUSES = get_statuses_from_env("TASK_NEW_STATUSES", ["new"])

ISSUE_DONE_STATUSES = get_statuses_from_env("ISSUE_DONE_STATUSES", ["done"])
ISSUE_IN_PROGRESS_STATUSES = get_statuses_from_env(
    "ISSUE_IN_PROGRESS_STATUSES", ["in progress"]
)
ISSUE_NEW_STATUSES = get_statuses_from_env("ISSUE_NEW_STATUSES", ["new"])


def filter_relevant_epics(epics, now=None):
    """Return only epics that are open, or closed but modified within N days."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=EPIC_DAYS_AFTER_CLOSE)
    relevant = []
    for epic in epics:
        if not epic.get("is_closed", False):
            relevant.append(epic)
        else:
            modified = datetime.strptime(epic["modified_date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if modified >= cutoff:
                relevant.append(epic)
    return relevant


def filter_relevant_issues(issues, now=None):
    """Return only issues that are open, or closed and completed within N days."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=ISSUE_DAYS_AFTER_CLOSE)
    relevant = []
    for issue in issues:
        # 'is_closed' should be True/False in Taiga data
        if not issue.get("is_closed", False):
            relevant.append(issue)
        else:
            # Check finished_date; fallback to modified_date if not set
            finished = (
                issue.get("finished_date")
                or issue.get("modified_date")
                or issue.get("created_date")
            )
            # Handle both with and without microseconds
            try:
                dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%SZ")
            if dt >= cutoff:
                relevant.append(issue)
    return relevant


def filter_relevant_userstories(stories, now=None):
    """Return only user stories that are open, or closed and completed within N days."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=USER_STORY_DAYS_AFTER_CLOSE)
    relevant = []
    for story in stories:
        if not story.get("is_closed", False):
            relevant.append(story)
        else:
            finished = (
                story.get("finish_date")
                or story.get("modified_date")
                or story.get("created_date")
            )
            try:
                dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%SZ")
            if dt >= cutoff:
                relevant.append(story)
    return relevant


def filter_relevant_tasks(tasks, now=None):
    """Return only tasks that are open, or closed and completed within N days."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=TASK_DAYS_AFTER_CLOSE)
    relevant = []
    for task in tasks:
        if not task.get("is_closed", False):
            relevant.append(task)
        else:
            finished = (
                task.get("finished_date")
                or task.get("modified_date")
                or task.get("created_date")
            )
            try:
                dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dt = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%SZ")
            if dt >= cutoff:
                relevant.append(task)
    return relevant


def get_epic_progress_html(epics, userstories):
    """
    Takes Taiga API lists of epics and user stories.
    Returns HTML for a Plotly stacked horizontal bar chart showing epic progress:
    - Green: percent of user stories Done/Closed
    - Orange: percent of user stories In Progress (customizable status names)
    - Gray: percent Not Started
    Also displays: epic status, total stories, and story counts per section.
    """
    # Filter epics to only those that are relevant (not closed or recently modified)
    epics = filter_relevant_epics(epics)

    # Map epic id to epic name for ordering and display
    epic_id_to_name = {epic["id"]: epic["subject"] for epic in epics}
    epic_id_to_status = {
        epic["id"]: epic.get("status_extra_info", {}).get("name", "") for epic in epics
    }
    epic_ids = [epic["id"] for epic in epics]
    epic_names = [epic_id_to_name[eid] for eid in epic_ids]

    # Build a mapping: epic_id -> list of user stories
    epic_to_stories = {eid: [] for eid in epic_ids}
    for us in userstories:
        # Taiga user stories: 'epics' is a list of dicts (can also be None)
        epics_field = us.get("epics")
        if isinstance(epics_field, list):
            for epic_ref in epics_field:
                eid = epic_ref.get("id")
                if eid in epic_to_stories:
                    epic_to_stories[eid].append(us)

    # Compute stacked bar percentages and counts for each epic
    done_perc, in_progress_perc, not_started_perc = [], [], []
    done_counts, in_progress_counts, not_started_counts = [], [], []
    total_counts = []
    y_labels = []  # this will include subject, (epic status), and total stories

    for eid in epic_ids:
        stories = epic_to_stories[eid]
        total = len(stories)
        total_counts.append(total)
        done_count = 0
        in_progress_count = 0
        new_count = 0  # not used for bar color, but available for future
        for s in stories:
            status = (s.get("status_extra_info", {}).get("name") or "").strip().lower()
            if status in USER_STORY_DONE_STATUSES:
                done_count += 1
            elif status in USER_STORY_IN_PROGRESS_STATUSES:
                in_progress_count += 1
            elif status in USER_STORY_NEW_STATUSES:
                new_count += 1
        not_started_count = total - done_count - in_progress_count

        # Percentages (avoid div by zero)
        done_perc.append(100 * done_count / total if total else 0)
        in_progress_perc.append(100 * in_progress_count / total if total else 0)
        not_started_perc.append(100 * not_started_count / total if total else 100)

        done_counts.append(done_count)
        in_progress_counts.append(in_progress_count)
        not_started_counts.append(not_started_count)

        # Build y label: Epic name (Status) [Stories: N]
        epic_status = epic_id_to_status.get(eid, "")
        # label = f"{epic_id_to_name[eid]} ({epic_status}) [{total}]"
        label = f"{epic_id_to_name[eid]}"
        y_labels.append(label)

    # Bar segment text (percent + count)
    done_text = [
        f"{perc:.0f}% ({count}/{total})" if total else "0% (0/0)"
        for perc, count, total in zip(done_perc, done_counts, total_counts)
    ]
    in_progress_text = [
        f"{perc:.0f}% ({count}/{total})" if total else "0% (0/0)"
        for perc, count, total in zip(
            in_progress_perc, in_progress_counts, total_counts
        )
    ]
    not_started_text = [
        f"{perc:.0f}% ({count}/{total})" if total else "0% (0/0)"
        for perc, count, total in zip(
            not_started_perc, not_started_counts, total_counts
        )
    ]

    bar_done = go.Bar(
        x=done_perc,
        y=y_labels,
        orientation="h",
        name="Completed",
        marker=dict(color="green"),
        text=done_text,
        textposition="inside",
    )
    bar_in_progress = go.Bar(
        x=in_progress_perc,
        y=y_labels,
        orientation="h",
        name="In Progress",
        marker=dict(color="orange"),
        text=in_progress_text,
        textposition="inside",
    )
    bar_not_started = go.Bar(
        x=not_started_perc,
        y=y_labels,
        orientation="h",
        name="Not Started",
        marker=dict(color="lightgray"),
        text=not_started_text,
        textposition="inside",
    )

    layout = go.Layout(
        title="Epics Progress Overview",
        xaxis=dict(title="Progress (%)", range=[0, 100]),
        yaxis=dict(title="Epic"),
        barmode="stack",
        height=50 * max(1, len(y_labels)),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    fig = go.Figure(data=[bar_done, bar_in_progress, bar_not_started], layout=layout)
    epic_progress_bar_html = plotly.io.to_html(
        fig, include_plotlyjs="cdn", full_html=False
    )
    return epic_progress_bar_html


def classify_sprints(sprints, today=None):
    """Classify sprints into active, future, completed based on estimated_start/finish and closed.
    Returns (active, future, completed) as lists of sprint dicts."""
    if today is None:
        today = datetime.utcnow().date()
    active = []
    future = []
    completed = []
    for sprint in sprints:
        start = datetime.strptime(sprint["estimated_start"], "%Y-%m-%d").date()
        end = datetime.strptime(sprint["estimated_finish"], "%Y-%m-%d").date()
        if start <= today <= end and not sprint.get("closed", False):
            active.append(sprint)
        elif start > today:
            future.append(sprint)
        elif end < today or sprint.get("closed", False):
            completed.append(sprint)
    # Sort for display: future by start, completed by finish descending
    future.sort(key=lambda s: s["estimated_start"])
    completed.sort(key=lambda s: s["estimated_finish"], reverse=True)
    active.sort(key=lambda s: s["estimated_start"])
    return active, future, completed


def filter_sprints_for_chart(sprints, num_future, num_completed):
    active, future, completed = classify_sprints(sprints)
    # For chart: all active, N future, N completed
    show_sprints = []
    show_sprints.extend(active)
    show_sprints.extend(future[:num_future])
    show_sprints.extend(completed[:num_completed])
    show_sprint_ids = {s["id"] for s in show_sprints}
    return show_sprints, show_sprint_ids


def sprint_status(sprint, today=None):
    """Return a human label for sprint status: Active, Future, Completed, Closed."""
    if today is None:
        today = datetime.utcnow().date()
    start = datetime.strptime(sprint["estimated_start"], "%Y-%m-%d").date()
    end = datetime.strptime(sprint["estimated_finish"], "%Y-%m-%d").date()
    if sprint.get("closed", False):
        return "Closed"
    if start <= today <= end:
        return "Active"
    elif start > today:
        return "Future"
    elif end < today:
        return "Completed"
    return "Unknown"


def format_date_range(start, end):
    """Format a date range as MM/dd/yy to MM/dd/yy"""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    return f"{start_dt.strftime('%m/%d/%y')} to {end_dt.strftime('%m/%d/%y')}"


def get_task_status_breakdown_html(userstories, tasks, issues, sprints, title):
    """
    Returns HTML for a stacked bar chart:
      - X-axis: sprint names (filtered: No Sprint, then active/future/completed ordered by start date)
      - Each bar: counts of user stories, tasks, and issues in each status per group
      - Bar order: Done (bottom), In Progress (middle), New (top)
      - Sprint label: name\nYYYY-MM-DD to YYYY-MM-DD\nStatus
    """
    # Filter sprints to active, next, most recent completed
    show_sprints, show_sprint_ids = filter_sprints_for_chart(sprints, 1, 2)
    today = datetime.utcnow().date()
    # Build mapping: sprint id -> sprint object
    sprint_id_to_obj = {s["id"]: s for s in show_sprints}

    # Only show these sprints and "No Sprint"
    all_items = []

    # Helper to append user story, task, or issue with normalized milestone (sprint)
    def add_item(item, milestone_field, item_type):
        group_id = item.get(milestone_field)
        all_items.append((group_id, item, item_type))

    for us in userstories:
        add_item(us, "milestone", "userstory")
    for t in tasks:
        add_item(t, "milestone", "task")
    for iss in issues:
        add_item(iss, "milestone", "issue")

    group_ids = set([gid for gid, _, _ in all_items if gid in sprint_id_to_obj])
    # Always include "No Sprint" if present
    if any(gid is None for gid, _, _ in all_items):
        group_ids.add(None)

    # Order sprints: No Sprint left, then by start date ascending
    ordered_group_ids = []
    if None in group_ids:
        ordered_group_ids.append(None)
    sorted_sprints = sorted(
        (sprint_id_to_obj[gid] for gid in group_ids if gid is not None),
        key=lambda s: s["estimated_start"],
    )
    ordered_group_ids.extend([s["id"] for s in sorted_sprints])

    # Build x labels with name, date range, and status
    group_labels = []
    for gid in ordered_group_ids:
        if gid is None:
            group_labels.append("No Sprint")
        else:
            sprint = sprint_id_to_obj[gid]
            name = sprint["name"]
            date_range = format_date_range(
                sprint["estimated_start"], sprint["estimated_finish"]
            )
            status = sprint_status(sprint, today)
            group_labels.append(f"{name}<br>{date_range}<br>{status}")

    # Main counts: group_id -> counts by status
    group_counts = defaultdict(lambda: {"Done": 0, "In Progress": 0, "New": 0})

    # Helper for status categorization
    def get_status_bucket(item, done_statuses, in_progress_statuses, new_statuses):
        status_raw = (
            (item.get("status_extra_info", {}).get("name") or "").strip().lower()
        )
        if status_raw in [s.lower() for s in done_statuses]:
            return "Done"
        elif status_raw in [s.lower() for s in in_progress_statuses]:
            return "In Progress"
        else:
            return "New"

    for group_id, item, item_type in all_items:
        # Only count if in our filtered set or it's "No Sprint"
        if group_id not in sprint_id_to_obj and group_id is not None:
            continue
        if item_type == "userstory":
            bucket = get_status_bucket(
                item,
                USER_STORY_DONE_STATUSES,
                USER_STORY_IN_PROGRESS_STATUSES,
                USER_STORY_NEW_STATUSES,
            )
        elif item_type == "task":
            bucket = get_status_bucket(
                item,
                TASK_DONE_STATUSES,
                TASK_IN_PROGRESS_STATUSES,
                TASK_NEW_STATUSES,
            )
        elif item_type == "issue":
            bucket = get_status_bucket(
                item,
                ISSUE_DONE_STATUSES,
                ISSUE_IN_PROGRESS_STATUSES,
                ISSUE_NEW_STATUSES,
            )
        else:
            bucket = "New"
        group_counts[group_id][bucket] += 1

    done_counts = [group_counts[gid]["Done"] for gid in ordered_group_ids]
    in_progress_counts = [group_counts[gid]["In Progress"] for gid in ordered_group_ids]
    new_counts = [group_counts[gid]["New"] for gid in ordered_group_ids]

    traces = [
        go.Bar(
            x=group_labels,
            y=done_counts,
            name="Done",
            marker=dict(color="green"),
            text=[str(n) if n > 0 else "0" for n in done_counts],
            textposition="inside",
            insidetextanchor="middle",
            textangle=0
        ),
        go.Bar(
            x=group_labels,
            y=in_progress_counts,
            name="In Progress",
            marker=dict(color="orange"),
            text=[str(n) if n > 0 else "0" for n in in_progress_counts],
            textposition="inside",
            insidetextanchor="middle",
            textangle=0
        ),
        go.Bar(
            x=group_labels,
            y=new_counts,
            name="New",
            marker=dict(color="lightgray"),
            text=[str(n) if n > 0 else "0" for n in new_counts],
            textposition="inside",
            insidetextanchor="middle",
            textangle=0
        ),
    ]

    layout = go.Layout(
        title=title,
        xaxis=dict(title="Sprint"),
        yaxis=dict(
            title="Number of Items",
            tickmode="linear",
            tick0=0,
            dtick=1,
        ),
        barmode="stack",
        height=500 if len(group_labels) < 10 else 80 * len(group_labels),
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig = go.Figure(data=traces, layout=layout)
    return plotly.io.to_html(fig, include_plotlyjs="cdn", full_html=False)


def get_task_assignment_heatmap_html(
    users, userstories, tasks, issues, column_metric="status"
):
    """
    Returns an HTML div containing a Plotly assignment heatmap based on users, userstories, tasks, and issues.
    Assumes *_STATUSES variables are defined in the outer scope.
    """

    # Filter relevant items
    userstories = filter_relevant_userstories(userstories)
    tasks = filter_relevant_tasks(tasks)
    issues = filter_relevant_issues(issues)

    # --- Build user lookup ---
    user_lookup = {
        u["id"]: u.get("full_name_display") or u.get("full_name") or u.get("username")
        for u in users
    }
    user_lookup[None] = "Unassigned"

    # --- Helper to get assignee name ---
    def get_assignee(obj):
        assignee_id = obj.get("assigned_to")
        return user_lookup.get(assignee_id, "Unassigned")

    # --- Helper to get status or priority ---
    def get_status(obj):
        info = obj.get("status_extra_info")
        if info and isinstance(info, dict):
            return info.get("name", "Unknown")
        return str(obj.get("status", "Unknown"))

    def get_priority(obj):
        info = obj.get("priority_extra_info")
        if info and isinstance(info, dict):
            return info.get("name", "Normal")
        return str(obj.get("priority", "Normal"))

    # --- Mapping to Not Started, In Progress, Done ---
    def map_to_bucket(status, done, in_progress, not_started):
        s = str(status).strip().lower()
        if s in [d.lower() for d in done]:
            return "Done"
        elif s in [p.lower() for p in in_progress]:
            return "In Progress"
        elif s in [n.lower() for n in not_started]:
            return "Not Started"
        else:
            return "Not Started"

    # --- Flatten all items to assignee/metric ---
    items = []
    for us in userstories:
        assignee = get_assignee(us)
        status_val = get_status(us) if column_metric == "status" else get_priority(us)
        bucket = (
            map_to_bucket(
                status_val,
                USER_STORY_DONE_STATUSES,
                USER_STORY_IN_PROGRESS_STATUSES,
                USER_STORY_NEW_STATUSES,
            )
            if column_metric == "status"
            else status_val
        )
        items.append((assignee, bucket))
    for t in tasks:
        assignee = get_assignee(t)
        status_val = get_status(t) if column_metric == "status" else get_priority(t)
        bucket = (
            map_to_bucket(
                status_val,
                TASK_DONE_STATUSES,
                TASK_IN_PROGRESS_STATUSES,
                TASK_NEW_STATUSES,
            )
            if column_metric == "status"
            else status_val
        )
        items.append((assignee, bucket))
    for iss in issues:
        assignee = get_assignee(iss)
        status_val = get_status(iss) if column_metric == "status" else get_priority(iss)
        bucket = (
            map_to_bucket(
                status_val,
                ISSUE_DONE_STATUSES,
                ISSUE_IN_PROGRESS_STATUSES,
                ISSUE_NEW_STATUSES,
            )
            if column_metric == "status"
            else status_val
        )
        items.append((assignee, bucket))

    # --- Build sorted lists of users and metrics (columns) ---
    assignees = sorted(set([a for a, _ in items if a != "Unassigned"]))
    if "Unassigned" not in assignees:
        assignees.append("Unassigned")
    else:
        assignees = [a for a in assignees if a != "Unassigned"] + ["Unassigned"]

    if column_metric == "status":
        COLUMNS = ["Not Started", "In Progress", "Done"]
    else:
        COLUMNS = sorted(set([m for _, m in items]))

    df = pd.DataFrame(items, columns=["assignee", "metric"])
    heatmap_df = (
        df.groupby(["assignee", "metric"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=assignees, columns=COLUMNS, fill_value=0)
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_df.values,
            x=heatmap_df.columns,
            y=heatmap_df.index,
            colorscale="Blues",
            hoverongaps=False,
            text=heatmap_df.values,
            texttemplate="%{text}",
            colorbar=dict(title="Task Count"),
        )
    )
    fig.update_layout(
        title="Task Assignment Heatmap",
        xaxis_title=(
            column_metric.capitalize() if column_metric != "status" else "Status"
        ),
        yaxis_title="Assignee",
        autosize=True,
        margin=dict(l=60, r=40, t=60, b=60),
        template="simple_white",
        height=max(350, 30 * len(assignees) + 120),
    )
    return fig.to_html(include_plotlyjs="cdn", full_html=False)