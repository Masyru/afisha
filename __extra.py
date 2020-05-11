import requests
import json
from lxml import html
import random
import tmdbsimple as tm
from requests import HTTPError

APIKEY = "AAAA_BBBB"


class RequestServer:
    def __init__(self, server):
        self.server = server

    def open_full(self, data):
        response = requests.post(f"{self.server}/full_description",
                                 json=data, verify=False)
        if not response.status_code >= 400:
            key = json.loads(response.text)["key"]
            return f"{self.server}/film/{key}"
        return None

    def create_new(self, chat_id):
        response = requests.get(f"{self.server}/api/maintain_users/?apikey={APIKEY}&method=new&chat_id={chat_id}", verify=False)
        if not response.status_code >= 400:
            return json.loads(response.text)
        return None

    def delete_user(self,  chat_id):
        response = requests.get(f"{self.server}/api/maintain_users/?apikey={APIKEY}&method=delete&chat_id={chat_id}", verify=False)
        if not response.status_code >= 400:
            return json.loads(response.text)
        return None

    def get_user(self, chat_id):
        response = requests.get(f"{self.server}/api/maintain_users/?apikey={APIKEY}&method=user_info&chat_id={chat_id}", verify=False)
        if not response.status_code >= 400:
            return json.loads(response.text)
        return None

    def change_state(self, chat_id, state):
        response = requests.get(
            f"{self.server}/api/maintain_users/?apikey={APIKEY}&method=state&chat_id={chat_id}&state={state}", verify=False)
        if not response.status_code >= 400:
            return json.loads(response.text)
        return None

    def change_some_fields(self, chat_id, data):
        response = requests.post(f"{self.server}/api/maintain_users/?apikey={APIKEY}&method=change&chat_id={chat_id}",
                                 json=data, verify=False)
        if not response.status_code >= 400:
            return json.loads(response.text)
        return None

    def check_existing(self, chat_id):
        response = requests.get(
            f"{self.server}/api/maintain_users/?apikey={APIKEY}&method=exist&chat_id={chat_id}", verify=False)
        if not response.status_code >= 400:
            return json.loads(response.text)
        return None


class TMDB:
    def __init__(self, config):
        self.config = config
        self.token = self.config["DEFAULT"]["token"]
        self.image_path = "https://image.tmdb.org/t/p/w600_and_h900_bestv2/"
        self.none_image = "http://www.fonstola.ru/pic/201409/640x960/fonstola.ru-149050.jpg"
        self.tm = tm
        self.tm.API_KEY = self.token

    def search_film(self, search_string):
        search = self.tm.Search()
        search.movie(query=search_string)
        data = list()
        for s in search.results:
            obj = dict()
            # noinspection PyBroadException
            try:
                try:
                    obj["release_date"] = s["release_date"] if len(s["release_date"]) != 0 else None
                except KeyError:
                    obj["release_date"] = None
                obj["title"] = s["title"]
                obj["description"] = s["overview"]
                obj["rate"] = s["popularity"]
                obj["vote_average"] = s["vote_average"]
                try:
                    obj["poster"] = self.image_path + s["poster_path"][1:]
                except TypeError:
                    obj["poster"] = self.none_image
                data.append(obj)
            except Exception:
                continue
        if not len(data):
            return None
        return data

    def ten_random_films(self):
        films = list()
        # noinspection PyBroadException

        while not len(films):
            ids = list()
            for _ in range(10):
                number = random.randint(1, 500000)
                while number in ids:
                    number = random.randint(1, 500000)
                ids.append(number)
            for _ in ids:
                obj = dict()
                try:
                    movie = self.tm.Movies(_)
                    response = movie.info()
                except HTTPError:
                    continue
                # noinspection PyBroadException
                try:
                    obj["release_date"] = response["release_date"] if len(response["release_date"]) != 0 else None
                except KeyError:
                    obj["release_date"] = None
                obj["title"] = response["title"]
                obj["description"] = response["overview"]
                obj["rate"] = response["popularity"]
                obj["vote_average"] = response["vote_average"]
                try:
                    obj["poster"] = self.image_path + response["poster_path"][1:]
                except TypeError:
                    obj["poster"] = self.none_image
                films.append(obj)
        return films

    def popular_films(self):
        url = "https://www.themoviedb.org/movie"
        with open("popular.txt", "wb") as fout:
            fout.write(requests.get(url).text.encode("utf-8"))

        with open("popular.txt", 'rb') as fin:
            page = fin.read()
            page = page.decode("utf-8")
        tree = html.fromstring(page)
        div_node = tree.get_element_by_id("page_1").find_class("card style_1")
        ids = list()
        films = list()
        for div in div_node:
            try:
                link = div.xpath('.//div[@class = "content"]/h2/a/@href')[0]
                ids.append(int(link.split("/")[-1]))
            except IndexError:
                break
        for _ in ids:
            obj = dict()
            try:
                movie = self.tm.Movies(_)
                response = movie.info()
            except HTTPError:
                continue
            # noinspection PyBroadException
            try:
                obj["release_date"] = response["release_date"] if len(response["release_date"]) != 0 else None
            except KeyError:
                obj["release_date"] = None
            obj["title"] = response["title"]
            obj["description"] = response["overview"]
            obj["rate"] = response["popularity"]
            obj["vote_average"] = response["vote_average"]
            try:
                obj["poster"] = self.image_path + response["poster_path"][1:]
            except TypeError:
                obj["poster"] = self.none_image
            films.append(obj)
        return films
