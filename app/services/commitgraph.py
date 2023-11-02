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
from typing import Dict, Any, Tuple, List, Optional
from io import IOBase


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


class InvalidUsernameAndRepositoryCombination(Exception):
    """Exception raised when provided username is not found by Github API."""

    pass


def check_valid_user_and_repo(owner: str, repo: str) -> Dict[str, Any]:
    """
    Checks if provided github user and repository are stored in firestore cache, if not make
    an API call to GitHub to check if username/repo are valid.

    Args:
        owner (str): The owner's username of the GitHub repository.
        repo (str): The repository name on GitHub.

    Returns:
        Dict[str, Any]: A dictionary containing "owner" and "repo" keys if valid.

    Raises:
        InvalidUsernameAndRepositoryCombination: If the owner/repo combination is invalid.
    """
    cache_key: str = f"{owner}_{repo}"

    # Attempt to fetch data from the cache
    doc_ref = db.collection("cache").document(cache_key)
    doc = doc_ref.get()

    if doc.exists:
        print(f"Cache hit for owner={owner}, repo={repo}")
        user_and_repo_info = doc.to_dict()
    else:
        print(
            f"No cache found for owner={owner}, repo={repo}. Making API call to GitHub."
        )

        github_api_username_repo_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}"
        )

        # If both requests are successful, we assume the user and repo are valid
        if github_api_username_repo_response.status_code == 200:
            user_and_repo_info = {"owner": owner, "repo": repo}
            # Store the result of your API call in cache
            doc_ref.set(user_and_repo_info)
        else:
            print(f"Invalid owner={owner} or repo={repo}.")
            raise InvalidUsernameAndRepositoryCombination

    return user_and_repo_info


def fetch_commits_from_api(
    base_url: str, page: int, per_page: int, start_date: Optional[date]
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Fetch a list of commits from the GitHub API.

    Args:
        base_url (str): The base URL for the GitHub API request.
        page (int): The page number to fetch from the GitHub API.
        per_page (int): The number of items per page to be fetched.
        start_date (date, optional): The start date from which to fetch commits.

    Returns:
        Tuple[List[Dict[str, Any]], Optional[str]]: A tuple with the list of commits
        and the 'Link' header from the response which contains pagination links.
    """
    params = {"page": page, "per_page": per_page}
    if start_date:
        params["since"] = start_date.isoformat()
    response = requests.get(base_url, params=params)
    return response.json(), response.headers.get("Link")


def count_commits_by_date(
    commits: List[Dict[str, Any]], commit_count: Dict[date, int]
) -> Dict[date, int]:
    """
    Count the number of commits by date from a list of commits.

    Args:
        commits (List[Dict[str, Any]]): A list of commits from the GitHub API.
        commit_count (Dict[date, int]): A dictionary to keep track of commit counts by date.

    Returns:
        Dict[date, int]: The updated dictionary with commit counts by date.
    """
    for commit in commits:
        date = commit["commit"]["committer"]["date"]
        date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").date()
        commit_count[date_obj] = commit_count.get(date_obj, 0) + 1
    return commit_count


def aggregate_commits_by_month(
    commit_count: Dict[date, int], period: str
) -> Dict[date, int]:
    """
    Aggregate commit counts by month based on the specified period.

    Args:
        commit_count (Dict[date, int]): The dictionary with commit counts by date.
        period (str): The time period to aggregate by ('year', 'all').

    Returns:
        Dict[date, int]: The dictionary with aggregated commit counts by the first day of each month.
    """
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


def get_date_range(period: str) -> Tuple[Optional[date], date]:
    """
    Determine the start and end dates for a given period.

    Args:
        period (str): A string representing the period ('month', 'year', or 'all').

    Returns:
        Tuple[Optional[date], date]: A tuple containing the start date and the end date.
    """
    end_date = datetime.now().date()
    days = PERIOD_DAYS.get(period)
    start_date = end_date - timedelta(days=days) if days else None
    return start_date, end_date


def initialize_commit_count(start_date: date, days: int) -> OrderedDict:
    """
    Initialize an ordered dictionary to count commits for each day starting from a date.

    Args:
        start_date (date): The date from which to start the count.
        days (int): The number of days for which to initialize the count.

    Returns:
        OrderedDict: An ordered dictionary with dates as keys and commit counts as values.
    """
    commit_count = OrderedDict()
    for day_number in range(days):
        day = start_date + timedelta(days=day_number)
        commit_count[day] = 0
    return commit_count


def fetch_all_commits(base_url: str, start_date: date) -> List[Dict[str, Any]]:
    """
    Fetch all commits from a GitHub repository starting from a specific date.

    Args:
        base_url (str): The GitHub API base URL for the commits endpoint.
        start_date (date): The date from which to start fetching commits.

    Returns:
        List[Dict[str, Any]]: A list of commit data in dictionary format.
    """
    commits = []
    page = 1
    per_page = 100
    while True:
        page_commits, next_page_link = fetch_commits_from_api(
            base_url, page, per_page, start_date
        )
        commits.extend(page_commits)
        if not page_commits or next_page_link is None:
            break
        page += 1
    return commits


def parse_commits(
    commits: List[Dict[str, Any]], commit_count: OrderedDict
) -> OrderedDict:
    """
    Parse the commit data and count the number of commits per day.

    Args:
        commits (List[Dict[str, Any]]): A list of commits from the GitHub API.
        commit_count (OrderedDict): An ordered dictionary to track the number of commits per day.

    Returns:
        OrderedDict: The updated commit count dictionary.
    """
    for commit in commits:
        commit_date_str = commit["commit"]["committer"]["date"]
        commit_date = datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%S%z").date()
        if commit_date in commit_count:
            commit_count[commit_date] += 1
    return commit_count


def aggregate_commit_data(commit_count: OrderedDict, period: str) -> OrderedDict:
    """
    Aggregate commit data based on a specific time period.

    Args:
        commit_count (OrderedDict): The ordered dictionary with commit counts by date.
        period (str): The period for which to aggregate the data ('month', 'year', or 'all').

    Returns:
        OrderedDict: The aggregated commit data.
    """
    # Implementation for aggregating commits
    return commit_count


def validate_repository(owner: str, repo: str) -> None:
    """
    Validate if the given repository exists on GitHub.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.

    Raises:
        RepoNotFoundError: If the repository does not exist.
    """
    if check_valid_user_and_repo(owner, repo) is None:
        raise RepoNotFoundError(f"Repository {owner}/{repo} not found.")


def fetch_commit_count_per_day(owner: str, repo: str, period: str) -> OrderedDict:
    """
    Fetch the count of commits per day for a repository within a specified period.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        period (str): The period for which to fetch the commit count ('month', 'year', or 'all').

    Returns:
        OrderedDict: An ordered dictionary with dates as keys and commit counts as values.
    """
    validate_repository(owner, repo)
    base_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    start_date, end_date = get_date_range(period)
    days = (end_date - start_date).days
    commit_count = initialize_commit_count(start_date, days)
    commits = fetch_all_commits(base_url, start_date)
    commit_count = parse_commits(commits, commit_count)
    commit_count = aggregate_commit_data(commit_count, period)
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


def plot_commit_count(
    commit_count: Dict[date, int],
    file_object: IOBase,
    repo: str,
    theme: str,
    period: str,
):
    """
    Plots the commit count for a given repository, theme, and time period and saves it to a file.

    Args:
        commit_count (Dict[date, int]): The commit count data by date.
        file_object (IOBase): The file object to save the plot to.
        repo (str): The repository name for which to plot the commit count.
        theme (str): The theme of the plot.
        period (str): The time period to plot for.

    Raises:
        NoCommitsFoundError: If no commits were found for this repository in the specified time range.
    """
    if not commit_count:
        raise NoCommitsFoundError(
            "No commits were found for this repository in the specified time range."
        )

    theme_settings = set_theme(theme)
    plt.figure(figsize=(12, 6))

    t, smooth_counts, date_nums, counts = prepare_data_for_plotting(commit_count)

    if theme_settings.get("colormap", None) is not None:
        plot_with_colormap(t, smooth_counts, theme_settings)
    else:
        plot_without_colormap(
            t, smooth_counts, date_nums, counts, period, theme_settings
        )

    configure_x_axis(sorted(commit_count.keys()), period, theme_settings)
    configure_y_axis(period, theme_settings)

    set_labels_and_title(repo, theme_settings)

    save_plot(file_object)
