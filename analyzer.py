#!/usr/bin/python

import fire
from datetime import datetime
import time
from resources.pushshift import Pushshift
from resources.ascii import coffee
from prettytable import PrettyTable
import csv
from tkinter import filedialog
from tkinter import Tk


class Analyzer(object):
    """
    Main analyzer for Reddit Overlap Analyzer.
    """

    def __init__(self):
        self.pushshift_client = Pushshift()

    def _convert_date_to_unix_timestamp(self, date):
        if not isinstance(date, datetime):
            date = datetime.strptime(date, "%m/%d/%Y")
        date = datetime.date(date)
        unix_timestamp = time.mktime(date.timetuple())
        return int(unix_timestamp)

    def analyze(
        self,
        subreddit,
        start,
        end=None,
        output="table",
        top=5,
        submissions=1000,
        sort_by="users",
    ):
        """
        Analyzes specified subreddits and
        outputs overlapping subreddits in order
        from highest to lowest.
        :param subreddit: Subreddit to analyze.
        :param start: The start date for range to analyze.
        :param end: The end date for range to analyze (default: Now).
        :param output: Output location for data (default: Table in stdout).
        :param top: Number of top Subreddits to output.
        :param submissions: Number of submissions to get from
        specified subreddit.
        """

        if subreddit[0] + subreddit[1] == "r/":
            subreddit = subreddit[2:]

        print(f"Starting overlap analysis for r/{subreddit}.")

        if not isinstance(start, datetime):
            if "/" in start:
                start = self._convert_date_to_unix_timestamp(start)
            else:
                raise Exception("Unsupported date format provided.")

        if end is None:
            end = self._convert_date_to_unix_timestamp(datetime.now())
        elif "/" in end:
            end = self._convert_date_to_unix_timestamp(end)
        else:
            raise Exception("Unsupported date format provided.")

        submissions = self.pushshift_client.get_reddit_submissions(
            subreddit=subreddit, start=start, end=end, limit=submissions
        )
        unique_authors = []
        [
            unique_authors.append(x["author"])
            for x in submissions
            if x["author"] not in unique_authors
        ]

        print(
            f"Getting last 1000 submissions for {len(unique_authors)} users."
        )
        print(coffee)
        print("Go grab some coffee. This is going to be a while.")

        authors = {}
        subreddits = {}

        for author in unique_authors:
            try:
                submissions = self.pushshift_client.get_reddit_submissions(
                    author=author
                )
                authors[author] = submissions
            except ConnectionError:
                time.sleep(54)
                continue

            for submission in submissions:
                try:
                    if submission["subreddit"] not in subreddits:
                        subreddits[submission["subreddit"]] = {
                            "submissions": [],
                            "authors": [],
                        }
                except KeyError:
                    if submission["promoted"]:
                        continue

                subreddits[submission["subreddit"]]["submissions"].append(
                    submission
                )
                if (
                    author
                    not in subreddits[submission["subreddit"]]["authors"]
                ):
                    subreddits[submission["subreddit"]]["authors"].append(
                        author
                    )
            # time.sleep(1)

        if subreddit in subreddits:
            subreddits.pop(subreddit, None)

        if output.lower() == "csv":
            start = datetime.fromtimestamp(start).strftime("%Y-%m-%d")
            end = datetime.fromtimestamp(end).strftime("%Y-%m-%d")
            root = Tk()
            root.filename = filedialog.askdirectory(
                initialdir="/", title="Select file"
            )

            file_name = subreddit + "-" + str(start) + "-" + str(end)
            file_path = root.filename + "/" + file_name
            with open(f"{file_path}.csv", mode="w") as csv_file:
                field_names = ["Subreddit", "Submission Count", "Unique Users"]
                writer = csv.writer(csv_file, delimiter="|")
                writer.writerow(field_names)
                for collected_subreddit in subreddits:
                    writer.writerow(
                        [
                            collected_subreddit,
                            len(
                                subreddits[collected_subreddit]["submissions"]
                            ),
                            len(subreddits[collected_subreddit]["authors"]),
                        ]
                    )
        elif output.lower() == "table":
            results_table = PrettyTable()
            results_table.field_names = [
                "Subreddit",
                "Submission Count",
                "Unique Users",
            ]

            for collected_subreddit in subreddits:
                results_table.add_row(
                    [
                        collected_subreddit,
                        len(subreddits[collected_subreddit]["submissions"]),
                        len(subreddits[collected_subreddit]["authors"]),
                    ]
                )
        else:
            return "Unsupported output type"

            if sort_by == "users":
                results_table.sortby = "Unique Users"
            elif sort_by == "submissions" or sort_by == "posts":
                results_table.sortby = "Submission Count"
            elif sort_by == "subreddit":
                results_table.sortby = "Subreddit"
            else:
                raise Exception("Unsupported sort_by value provided.")

            results_table.reversesort = True

            print(
                results_table.get_string(
                    title=f"Overlapping Reddit Trends for r/{subreddit}",
                    start=0,
                    end=top,
                )
            )


if __name__ == "__main__":
    fire.Fire(Analyzer)
