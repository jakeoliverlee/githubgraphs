import requests
from datetime import datetime, timedelta, date
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MonthLocator, YearLocator
from matplotlib.ticker import MaxNLocator, MultipleLocator
import numpy as np
from flask import jsonify
from collections import OrderedDict
import matplotlib.cm as cm
from firebase_admin import firestore

db = firestore.Client()

THEMES = {
    "dark": {
        "style": "dark_background",
        "line_color": "dodgerblue",
        "fill_color": "dodgerblue",
        "fill_alpha": 0.2,
        "label_color": "white",
        "tick_color": "white",
    },
    "light": {
        "style": "seaborn-whitegrid",
        "line_color": "lightblue",
        "fill_color": "lightblue",
        "fill_alpha": 0.2,
        "label_color": "black",
        "tick_color": "black",
    },
    "sunset": {
        "style": "seaborn-darkgrid",
        "line_color": "darkorange",
        "fill_color": "gold",
        "fill_alpha": 0.3,
        "label_color": "black",
        "tick_color": "black",
    },
    "forest": {
        "style": "seaborn-darkgrid",
        "line_color": "darkgreen",
        "fill_color": "lightgreen",
        "fill_alpha": 0.2,
        "label_color": "black",
        "tick_color": "black",
    },
    "ocean": {
        "style": "seaborn-darkgrid",
        "line_color": "darkblue",
        "fill_color": "lightblue",
        "fill_alpha": 0.2,
        "label_color": "black",
        "tick_color": "black",
    },
    "sakura": {
        "style": "seaborn-whitegrid",
        "line_color": "deeppink",
        "fill_color": "lightpink",
        "fill_alpha": 0.2,
        "label_color": "black",
        "tick_color": "black",
    },
    "monochrome": {
        "style": "seaborn-whitegrid",
        "line_color": "black",
        "fill_color": "gray",
        "fill_alpha": 0.2,
        "label_color": "black",
        "tick_color": "black",
    },
    "rainbow": {
        "style": "seaborn-whitegrid",
        "colormap": cm.get_cmap("rainbow"),  # Using rainbow colormap
        "fill_alpha": 0.2,
        "label_color": "black",
        "tick_color": "black",
    },
}

PERIODS = ["month", "year", "all"]
PERIOD_DAYS = {
    "month": 30,
    "year": 365,
    "all": None,
}


class RepoNotFoundError(Exception):
    pass


class NoCommitsFoundError(Exception):
    pass


class InvalidUsername(Exception):
    """Exception raised when provided username is not found by Github API."""

    pass


def check_valid_user_and_repo(owner, repo):
    cache_key = f"{owner}_{repo}"
    
    # Attempt to fetch data from the cache
    doc_ref = db.collection('cache').document(cache_key)
    doc = doc_ref.get()

    if doc.exists:
        print(f"Cache hit for owner={owner}, repo={repo}")
        user_and_repo_info = doc.to_dict()
    else:
        print(f"No cache found for owner={owner}, repo={repo}. Making API call.")
        
        # Perform your API calls and processing here...
        response_user = requests.get(f"https://api.github.com/users/{owner}")
        response_repo = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
        
        # If both requests are successful, we assume the user and repo are valid
        if response_user.status_code == 200 and response_repo.status_code == 200:
            user_and_repo_info = {
                "owner": owner,
                "repo": repo
            }
            # Store the result of your API call in cache
            doc_ref.set(user_and_repo_info)
        else:
            print(f"Invalid owner={owner} or repo={repo}.")
            user_and_repo_info = None

    return user_and_repo_info





def fetch_commits_from_api(base_url, page, per_page, start_date):
    params = {"page": page, "per_page": per_page}
    if start_date is not None:
        params["since"] = start_date.isoformat()
    response = requests.get(base_url, params=params)
    return response.json()


def count_commits_by_date(commits, commit_count):
    for commit in commits:
        date = commit["commit"]["committer"]["date"]
        date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").date()
        commit_count[date_obj] = commit_count.get(date_obj, 0) + 1
    return commit_count


def aggregate_commits_by_month(commit_count, period):
    commit_count_monthly = OrderedDict()
    if period in ["year", "all"]:
        for date, count in commit_count.items():
            month = date.replace(day=1)  # Get the first day of the month
            if month not in commit_count_monthly:
                commit_count_monthly[month] = count
            else:
                commit_count_monthly[month] += count
        commit_count = commit_count_monthly
    return commit_count


def fetch_commit_count_per_day(owner, repo, period):
    if check_valid_user_and_repo(owner, repo) is None:
        raise RepoNotFoundError(f"Repository {owner}/{repo} not found.")
    
    base_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    # Initialize commit_count with zero counts for every day in the past 'period'
    end_date = datetime.now().date()
    days = PERIOD_DAYS.get(period)
    start_date = end_date - timedelta(days=days) if days else None
    commit_count = OrderedDict()

    # Initialize the commit count for every date in the period to zero
    if start_date is not None:
        for day_number in range(days):
            day = start_date + timedelta(days=day_number)
            commit_count[day] = 0

    page = 1
    per_page = 100

    while True:
        commits = fetch_commits_from_api(base_url, page, per_page, start_date)

        if not commits:
            break

        commit_count = count_commits_by_date(commits, commit_count)

        if len(commits) < per_page:
            break

        page += 1

    commit_count = aggregate_commits_by_month(commit_count, period)

    return commit_count


def set_theme(theme):
    theme_settings = THEMES.get(theme, THEMES["dark"])
    plt.rcdefaults()
    plt.style.use(theme_settings["style"])
    return theme_settings


def prepare_data_for_plotting(commit_count):
    dates = sorted(commit_count.keys())
    counts = [commit_count[date] for date in dates]
    date_nums = mdates.date2num(dates)
    t = np.linspace(date_nums.min(), date_nums.max(), 300)
    smooth_counts = np.interp(t, date_nums, counts)
    return t, smooth_counts, date_nums, counts


def plot_with_colormap(t, smooth_counts, theme_settings):
    colormap = theme_settings.get("colormap", None)
    if colormap is not None:
        for i in range(1, len(t)):
            color = colormap(i / len(t))
            plt.plot(t[i - 1 : i + 1], smooth_counts[i - 1 : i + 1], color=color)
            plt.fill_between(
                t[i - 1 : i + 1],
                smooth_counts[i - 1 : i + 1],
                color=color,
                alpha=theme_settings["fill_alpha"],
            )


def plot_without_colormap(t, smooth_counts, date_nums, counts, period, theme_settings):
    plt.plot(t, smooth_counts, color=theme_settings["line_color"])
    if period == "month":
        plt.plot(date_nums, counts, linestyle="", color=theme_settings["line_color"])
    plt.fill_between(
        t,
        smooth_counts,
        color=theme_settings["fill_color"],
        alpha=theme_settings["fill_alpha"],
    )


def configure_x_axis(dates, period, theme_settings):
    date_range = max(dates) - min(dates)
    if period == "all":
        if date_range > timedelta(days=365):
            plt.gca().xaxis.set_major_locator(YearLocator())
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        else:
            plt.gca().xaxis.set_major_locator(MonthLocator())
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    elif period == "year":
        plt.gca().xaxis.set_major_locator(MonthLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    else:
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=3))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d"))

    plt.xlabel("Time", color=theme_settings["label_color"])


def configure_y_axis(period, theme_settings):
    if period in ["year", "all"]:
        plt.gca().yaxis.set_major_locator(MultipleLocator(10))
    else:
        plt.gca().yaxis.set_major_locator(MultipleLocator(1))
    plt.yticks(color=theme_settings["tick_color"])
    plt.ylim(bottom=0)
    plt.ylabel("Commit Count", color=theme_settings["label_color"])


def set_labels_and_title(repo, theme_settings):
    plt.title(f"Commit Count for {repo}", color=theme_settings["label_color"])
    plt.xticks(rotation=45, ha="right", color=theme_settings["tick_color"])


def save_plot(file_object):
    plt.tight_layout()
    plt.savefig(file_object, format="svg", dpi=1200)
    plt.clf()


def plot_commit_count(commit_count, file_object, repo, theme, period):
    if not commit_count:
        raise NoCommitsFoundError("No commits were found for this repository in the specified time range.")
    
    theme_settings = set_theme(theme)
    plt.figure(figsize=(12, 6))

    t, smooth_counts, date_nums, counts = prepare_data_for_plotting(commit_count)

    if theme_settings.get("colormap", None) is not None:
        plot_with_colormap(t, smooth_counts, theme_settings)
    else:
        plot_without_colormap(t, smooth_counts, date_nums, counts, period, theme_settings)

    
    configure_x_axis(sorted(commit_count.keys()), period, theme_settings)
    configure_y_axis(period, theme_settings)
    
    set_labels_and_title(repo, theme_settings)
    
    save_plot(file_object)



