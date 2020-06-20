import requests
import time


class Pushshift(object):
    def __init__(self):
        self.base_url = "https://api.pushshift.io/"

    def _request(self, endpoint, params={}, headers={}):
        response = requests.get(self.base_url + endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            time.sleep(3)
            return self._request(endpoint, params=params, headers=headers)
        else:
            raise Exception(
                f"Received a {response.status_code} from Pushshift API."
            )

    def get_reddit_submissions(
        self, subreddit=None, start=None, end=None, author=None, limit=500
    ):
        endpoint = "reddit/search/submission"
        params = {
            "subreddit": subreddit,
            "after": start,
            "before": end,
            "size": limit,
            "author": author,
        }
        data = self._request(endpoint, params=params)
        return data["data"]
