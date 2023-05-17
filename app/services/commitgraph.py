import requests
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MonthLocator, YearLocator
from matplotlib.ticker import MaxNLocator, MultipleLocator
import numpy as np
from flask import jsonify
from collections import OrderedDict

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


from datetime import date, timedelta


def fetch_commit_count_per_day(owner, repo, period):
    response = requests.get(f"https://api.github.com/users/{owner}")
    if response.status_code != 200:
        raise InvalidUsername(f"Username does not exist on Github")
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
    if response.status_code != 200:
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
        params = {"page": page, "per_page": per_page}
        if start_date is not None:
            params["since"] = start_date.isoformat()
        response = requests.get(base_url, params=params)
        commits = response.json()

        if not commits:
            break

        for commit in commits:
            date = commit["commit"]["committer"]["date"]
            date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").date()
            commit_count[date_obj] = commit_count.get(date_obj, 0) + 1

        if len(commits) < per_page:
            break

        page += 1

    commit_count_monthly = OrderedDict()
    if period in ["year", "all"]:
        for date, count in commit_count.items():
            month = date.replace(day=1)  # Get the first day of the month
            if month not in commit_count_monthly:
                commit_count_monthly[month] = count
            else:
                commit_count_monthly[month] += count
        commit_count = (
            commit_count_monthly  # Replace commit_count with the monthly counts
        )

    return commit_count


from matplotlib.ticker import MaxNLocator


def plot_commit_count(commit_count, file_object, repo, theme, period):
    if not commit_count:
        raise NoCommitsFoundError(
            "No commits were found for this repository in the specified time range."
        )
    theme_settings = THEMES.get(theme, THEMES["dark"])  # Use dark theme as default
    plt.rcdefaults()  # Reset matplotlib settings to default.
    plt.style.use(theme_settings["style"])

    plt.figure(figsize=(12, 6))  # Create a new figure with specified width and height

    dates = sorted(commit_count.keys())
    counts = [commit_count[date] for date in dates]

    # Convert dates to numbers for interpolation
    date_nums = mdates.date2num(dates)

    # Perform linear interpolation
    t = np.linspace(date_nums.min(), date_nums.max(), 300)  # Define the range of t
    smooth_counts = np.interp(t, date_nums, counts)

    # Plot the smooth curve
    plt.plot(t, smooth_counts, color=theme_settings["line_color"])

    # Include markers only when period is 'month'
    if period == "month":
        plt.plot(
            date_nums,
            counts,
            linestyle="",
            color=theme_settings["line_color"],
        )

    # Fill the area below the curve with the chosen color
    plt.fill_between(
        t,
        smooth_counts,
        color=theme_settings["fill_color"],
        alpha=theme_settings["fill_alpha"],
    )

    date_range = max(dates) - min(dates)

    # Configure the x-axis
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
    plt.ylabel("Commit Count", color=theme_settings["label_color"])
    plt.title(f"Commit Count for {repo}", color=theme_settings["label_color"])
    plt.xticks(rotation=45, ha="right", color=theme_settings["tick_color"])

    # Set y-axis intervals to 10 commits when period is 'year' or 'all'
    if period in ["year", "all"]:
        plt.gca().yaxis.set_major_locator(MultipleLocator(10))
    else:
        plt.gca().yaxis.set_major_locator(MultipleLocator(1))
    plt.yticks(color=theme_settings["tick_color"])

    # Set the y-limit to start from 0
    plt.ylim(bottom=0)

    plt.tight_layout()  # Automatically adjust subplot parameters to give specified padding.

    # Save the plot to a file
    plt.savefig(file_object, format="svg", dpi=1200)
    # Clear the current figure to ensure that the next plot does not inherit the settings of the previous plot
    plt.clf()
