import requests
import json
import configparser
import webbrowser
import time
from pprint import pprint


class TMDB:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("settings.ini")
        self.token = self.config["DEFAULT"]["token"]
        response = requests.get(f"https://api.themoviedb.org/3/authentication/token/new?api_key={self.token}")
        if not response.status_code >= 400:
            self.request_token = json.loads(response.text)["request_token"]
            # webbrowser.open(f"https://www.themoviedb.org/authenticate/{self.request_token}")
            time.sleep(5)
        else:
            raise ConnectionError("The operation had not reached.")

    def search_film(self, search_string):
        response = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={self.token}&query={search_string}&include_adult=true")
        if response.status_code >= 400:
            response = json.loads(response.text)
            result = response["results"]
            return result
        else:
            pprint(json.loads(response.text)["status_message"])
            return None
