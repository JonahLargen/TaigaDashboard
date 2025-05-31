import plotly.graph_objs as go
import plotly
import os
from collections import defaultdict
from datetime import datetime


def get_statuses_from_env(var_name, default=None):
    """Read a comma-separated status list from env, return as a set of lowercased strings."""
    value = os.getenv(var_name)
    if value is None:
        return set(default or [])
    return set(v.strip().lower() for v in value.split(",") if v.strip())


DONE_STATUSES = get_statuses_from_env("USER_STORY_DONE_STATUSES", [])
IN_PROGRESS_STATUSES = get_statuses_from_env("USER_STORY_IN_PROGRESS_STATUSES", [])
NEW_STATUSES = get_statuses_from_env("USER_STORY_NEW_STATUSES", [])


def get_epic_progress_html(epics, userstories):
    """
    Takes Taiga API lists of epics and user stories.
    Returns HTML for a Plotly stacked horizontal bar chart showing epic progress:
    - Green: percent of user stories Done/Closed
    - Orange: percent of user stories In Progress (customizable status names)
    - Gray: percent Not Started
    Also displays: epic status, total stories, and story counts per section.
    """

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
            if status in DONE_STATUSES:
                done_count += 1
            elif status in IN_PROGRESS_STATUSES:
                in_progress_count += 1
            elif status in NEW_STATUSES:
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


def filter_sprints_for_chart(sprints, num_future=1, num_completed=1):
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


def get_user_story_status_breakdown_html(userstories, sprints):
    """
    Returns HTML for a stacked bar chart:
      - X-axis: sprint names (filtered: No Sprint, then active/future/completed ordered by start date)
      - Each bar: counts of user stories in each status per group
      - Bar order: Done (bottom), In Progress (middle), Not Started (top)
      - Sprint label: name\nYYYY-MM-DD to YYYY-MM-DD\nStatus
    """
    # Filter sprints to active, next, most recent completed
    show_sprints, show_sprint_ids = filter_sprints_for_chart(
        sprints, num_future=1, num_completed=1
    )
    today = datetime.utcnow().date()
    # Build mapping: sprint id -> sprint object
    sprint_id_to_obj = {s["id"]: s for s in show_sprints}

    # Only show these sprints and "No Sprint"
    group_ids = set(
        [
            us.get("milestone")
            for us in userstories
            if us.get("milestone") in sprint_id_to_obj
        ]
    )
    # Always include "No Sprint" if present
    if any(us.get("milestone") is None for us in userstories):
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
    group_counts = defaultdict(lambda: {"Done": 0, "In Progress": 0, "Not Started": 0})

    for us in userstories:
        group_id = us.get("milestone")
        # Only count if in our filtered set or it's "No Sprint"
        if group_id not in sprint_id_to_obj and group_id is not None:
            continue
        status_raw = (us.get("status_extra_info", {}).get("name") or "").strip().lower()
        if status_raw in DONE_STATUSES:
            group_counts[group_id]["Done"] += 1
        elif status_raw in IN_PROGRESS_STATUSES:
            group_counts[group_id]["In Progress"] += 1
        else:
            group_counts[group_id]["Not Started"] += 1

    done_counts = [group_counts[gid]["Done"] for gid in ordered_group_ids]
    in_progress_counts = [group_counts[gid]["In Progress"] for gid in ordered_group_ids]
    not_started_counts = [group_counts[gid]["Not Started"] for gid in ordered_group_ids]

    traces = [
        go.Bar(
            x=group_labels,
            y=done_counts,
            name="Done",
            marker=dict(color="green"),
            text=[str(n) if n > 0 else "0" for n in done_counts],
            textposition="inside",
            insidetextanchor="middle",
        ),
        go.Bar(
            x=group_labels,
            y=in_progress_counts,
            name="In Progress",
            marker=dict(color="orange"),
            text=[str(n) if n > 0 else "0" for n in in_progress_counts],
            textposition="inside",
            insidetextanchor="middle",
        ),
        go.Bar(
            x=group_labels,
            y=not_started_counts,
            name="Not Started",
            marker=dict(color="lightgray"),
            text=[str(n) if n > 0 else "0" for n in not_started_counts],
            textposition="inside",
            insidetextanchor="middle",
        ),
    ]

    layout = go.Layout(
        title="User Story Status Breakdown by Sprint",
        xaxis=dict(title="Sprint"),
        yaxis=dict(
            title="Number of User Stories",
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