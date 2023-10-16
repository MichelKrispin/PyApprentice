#!./venv/bin/python3
import os
import json

import tornado.ioloop
import tornado.web
import tornado.websocket

from shutil import copyfile


def save_data(d, v, file_name, cell_id, close=False):
    update_data(d, v, cell_id)
    copyfile(file_name, file_name + '.backup')
    with open(file_name, 'w') as f:
        json.dump(d, f)
    if close:
        os.remove(file_name + '.backup')


def load_data(file_name):
    with open(file_name, 'r') as f:
        loaded = json.load(f)
    return loaded


def update_data(d, v, cell_id):
    cell = None
    for c in d['cells']:
        if c['id'] == cell_id:
            c['code'] = v['code']
            c['text'] = v['text']
            c['check'] = v['check']
            c['title'] = v['title']
            return
    if not cell:
        print(f'{cell_id} does not exist. Highest is {get_highest_id(d)}')
        return


def get_highest_id(d):
    i = 0
    for c in d['cells']:
        if c['id'] > i:
            i = c['id']
    return i


def update_display(d, w, cell_id):
    cell = None
    for c in d['cells']:
        if c['id'] == cell_id:
            cell = c
            break
    if not cell:
        print(f'{cell_id} does not exist. Highest is {get_highest_id(d)}')
        return
    w['max-id'].update(f'Max ID: {get_highest_id(d)}')
    w['code'].update(cell['code'])
    w['text'].update(cell['text'])
    w['check'].update(cell['check'])
    w['title'].update(cell['title'])


def redo(event, text):
    try:
        text.edit_redo()
    except:
        pass

def search_for_notebooks(notebooks):
    for f in os.listdir('./Notebooks'):
        if f.endswith('.yaml'):
            notebooks[slugify(f[:-5])] = f

class HomeHandler(tornado.web.RequestHandler):
    def initialize(self, notebooks):
        self.notebooks = notebooks

    def get(self):
        search_for_notebooks(self.notebooks)
        file_information = []
        for k in self.notebooks.keys():
            notebook = {
                'url': self.reverse_url('notebook', k),
                'name': self.notebooks[k][:-5],
            }
            file_information.append(notebook)

        self.render("static/index.html", notebooks=file_information)

class RunWebSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, cell_handlers):
        self.cell_handler = cell_handlers[0]

    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message(self.cell_handler.send_as_str())

    def on_message(self, message):
        data = json.loads(message)
        self.cell_handler.check(data['global-code'], data['code'], data['id'])
        # print(f'{output}which is {result}\n')
        self.write_message(self.cell_handler.send_as_str())

    def on_close(self):
        self.cell_handler.save(close=True)
        print(f'{self.cell_handler.file_name} closed and saved.')


def make_app():
    notebooks = {}  # Very shady use of references...
    cell_handlers = []
    return tornado.web.Application([
        tornado.web.url(r'/', HomeHandler, dict(notebooks=notebooks), name='home'),
        tornado.web.url(r'/ws', RunWebSocket, dict(cell_handlers=cell_handlers)),
    ], static_path='./static')


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    webbrowser.open('http://localhost:8000/')
    tornado.ioloop.IOLoop.current().start()