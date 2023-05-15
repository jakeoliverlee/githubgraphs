import requests
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import make_interp_spline, BSpline
import numpy as np
from scipy.interpolate import PchipInterpolator


def fetch_commit_count_per_day(owner, repo):
    base_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commit_count = defaultdict(int)
    page = 1
    per_page = 100
    end_date = datetime.now()

    while True:
        params = {
            "page": page,
            "per_page": per_page,
            "since": (
                end_date - timedelta(days=30)
            ).isoformat(),  # Limit to the past month
        }
        response = requests.get(base_url, params=params)
        commits = response.json()

        if not commits:
            break

        for commit in commits:
            date = commit["commit"]["committer"]["date"]
            date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").date()
            commit_count[date_obj] += 1

        if len(commits) < per_page:
            break

        page += 1

    return commit_count


def plot_commit_count(commit_count, filename, repo, file_format):
    plt.style.use("dark_background")
    dates = sorted(commit_count.keys())
    counts = [commit_count[date] for date in dates]

    # Convert dates to numbers for interpolation
    date_nums = mdates.date2num(dates)

    # Perform PCHIP interpolation
    t = np.linspace(
        date_nums.min() - 1, date_nums.max() + 1, 300
    )  # Extend the range of t
    pchip = PchipInterpolator(date_nums, counts)
    smooth_counts = pchip(t)

    plt.figure(figsize=(12, 6))  # Create a new figure with specified width and height

    # Plot the smooth curve
    plt.plot(t, smooth_counts, color="dodgerblue")

    plt.plot(date_nums, counts, marker="o", linestyle="", color="dodgerblue")

    # Fill the area below the curve with blue color
    plt.fill_between(t, smooth_counts, color="dodgerblue", alpha=0.2)

    # Configure the x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d"))
    plt.gca().xaxis.set_major_locator(
        mdates.DayLocator(interval=3)
    )  # Set x-axis ticks to one every three days

    plt.xlabel("Days", color="white")
    plt.ylabel("Commit Count", color="white")
    plt.title(f"Commit Count for {repo}", color="white")
    plt.xticks(rotation=45, color="white")
    plt.yticks(color="white")

    # Save the plot to a file
    plt.savefig(filename, format=file_format, dpi=1200)
