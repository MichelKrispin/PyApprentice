#!./venv/bin/python3
import os
import json
import yaml

import webbrowser
import tornado.ioloop
import tornado.web
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
    def initialize(self):
        self.notebooks = []
        for f in os.listdir("../Notebooks"):
            if f.endswith(".yaml"):
                self.notebooks.append(f)

    def get(self):
        self.render("static/index.html", notebooks=self.notebooks)

    def post(self):
        args = self.request.arguments
        print(self.get_body_argument("fname", default=None, strip=False))

        self.render("static/index.html", notebooks=self.notebooks)


class NotebookHandler(tornado.web.RequestHandler):
    def get(self):
        notebook = self.request.arguments["notebook"][0].decode()
        with open(f"../Notebooks/{notebook}", "r") as f:
            data = yaml.safe_load(f)
        json_data = r = json.dumps(data)
        print(json_data)
        self.write(data)


def make_app():
    return tornado.web.Application(
        [
            tornado.web.url(r"/", HomeHandler, name="home"),
            tornado.web.url(r"/notebook", NotebookHandler, name="notebook"),
        ],
        static_path="./static",
        debug=True,
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8001)
    # webbrowser.open("http://localhost:8001/")
    tornado.ioloop.IOLoop.current().start()
[]
