import plotly.graph_objs as go
import plotly
import os


def get_statuses_from_env(var_name, default=None):
    """Read a comma-separated status list from env, return as a set of lowercased strings."""
    value = os.getenv(var_name)
    if value is None:
        return set(default or [])
    return set(v.strip().lower() for v in value.split(',') if v.strip())

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
        label = f"{epic_id_to_name[eid]} ({epic_status}) [{total}]"
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