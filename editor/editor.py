#!./venv/bin/python3
import os
import json
import sys

import webbrowser
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.websocket

import re
import unicodedata


def slugify(value):
    """
    From django
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub("[^\w\s-]", "", value).strip().lower()
    return re.sub("[-\s]+", "-", value)


class HomeHandler(tornado.web.RequestHandler):
    def initialize(self, notebook_search_path):
        self.notebooks = []
        for f in os.listdir(notebook_search_path):
            if f.endswith(".json"):
                self.notebooks.append(f)

    def get(self):
        self.render("static/index.html", notebooks=self.notebooks)


class NotebookHandler(tornado.web.RequestHandler):
    def initialize(self, notebook_search_path):
        self.notebook_search_path = notebook_search_path

    def get(self):
        notebook = self.request.arguments["notebook"][0].decode()
        with open(os.path.join(self.notebook_search_path, notebook), "r") as f:
            data = json.load(f)
        self.write(data)

    def post(self):
        response = tornado.escape.json_decode(self.request.body)
        filename = response["filename"]
        data = response["data"]
        with open(os.path.join(self.notebook_search_path, filename), "w") as f:
            json.dump(data, f)
        self.write({"success": True})


def make_app(notebook_search_path):
    return tornado.web.Application(
        [
            tornado.web.url(
                r"/",
                HomeHandler,
                dict(notebook_search_path=notebook_search_path),
                name="home",
            ),
            tornado.web.url(
                r"/notebook",
                NotebookHandler,
                dict(notebook_search_path=notebook_search_path),
                name="notebook",
            ),
        ],
        static_path="./static",
    )


if __name__ == "__main__":
    notebook_search_path = sys.argv[1] if len(sys.argv) > 1 else "../Notebooks/"
    if len(sys.argv) > 1:
        print(f"Searching for notebooks in '{notebook_search_path}'")
    app = make_app(notebook_search_path)
    app.listen(8001)
    webbrowser.open("http://localhost:8001/")
    print("\n  >> Starting at http://localhost:8001/ <<")
    tornado.ioloop.IOLoop.current().start()
