#!/usr/bin/env python3
import yaml
import json
import os
import re
import unicodedata
import webbrowser

import traceback
import tornado.ioloop
import tornado.web
import tornado.websocket

from shutil import copyfile
from io import StringIO
from contextlib import redirect_stdout

def str_presenter(dumper, data):
  if len(data.splitlines()) > 1:  # check for multiline string
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

# to use with safe_dump:
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

class CellHandler:
    def __init__(self, file_name):
        self.file_name = file_name  # 'Notebooks/beginner_.yaml'
        # Make a copy of the original file, if there is none
        if not os.path.isfile(self.file_name + '.original'):
            copyfile(self.file_name, self.file_name + '.original')
        with open(self.file_name, 'r') as f:
            self.data = yaml.safe_load(f)

    def send_as_str(self):
        return json.dumps(self.data)

    def save(self, close=False):
        """Save the data to file."""
        copyfile(self.file_name, self.file_name + '.backup')
        with open(self.file_name, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)
        if close:
            os.remove(self.file_name + '.backup')

    def check(self, global_code, code, id):
        """Runs the code sandboxed and
        calls the check function with the result.

        Args:
            global_code (str): The global code that will be run before.
            code (str): The code that will be run for the cell.
            id (int): The id of this cell.
        """
        # Get the correct cell or raise an exception if it doesn't exist
        cell = None
        for c in self.data['cells']:
            if c['id'] == id:
                cell = c
                break
        if not cell:
            raise IndexError(f'Id {id} not found in the cells')

        # Run the global code before the users code is run
        scope = {'__name__': 'global_code', '__builtins__': globals()['__builtins__']}
        caught_exception = False
        result = False
        output = ''
        message = ''
        if global_code != '':
            f = StringIO()
            with redirect_stdout(f):
                try:
                    exec(global_code, scope)
                except Exception as e:
                    exception = traceback.format_exc()
                    # Remove the traceback for the global code
                    lines = exception.split('\n')
                    output = '\n'.join([lines[0]] + lines[3:]) \
                        .replace('<string>', 'Global Code')
            caught_exception = output != ''
            output = output if caught_exception else f.getvalue()

            # If everything went right do a little bit of reflection magic
            # such that every function created in the global functions scope
            # knows where it comes from.
            for attr in scope:
                try:
                    if scope[attr].__code__.co_filename == '<string>':
                        scope[attr].__code__ = scope[attr].__code__.replace(co_filename='Global Code')
                except AttributeError:
                    pass
        # Run the code sent by the user in the same scope
        if not caught_exception:
            scope['__name__'] = '__main__'
            f = StringIO()
            with redirect_stdout(f):
                try:
                    exec(code, scope)
                except Exception as e:
                    exception = traceback.format_exc()
                    # Remove the traceback for this file
                    lines = exception.split('\n')
                    exercise_name = cell['title']
                    output = '\n'.join([lines[0]] + lines[3:]) \
                        .replace('<string>', exercise_name)
            caught_exception = output != ''
            output = output if caught_exception else f.getvalue()

            # Find the checking function
            check_code = cell['check']
            check_code += '\nresult = _Check(_Scope, _Output)'

            check_scope = {'__name__': '__main__',
                           '__builtins__': globals()['__builtins__'],
                           '_Scope': scope, '_Output': output}

            # Run the checking function in the created scope
            f = StringIO()
            with redirect_stdout(f):
                exec(check_code, check_scope)
            # print('------\n', f.getvalue(), '------\n')
            result, message = check_scope['result']

        # Save data
        self.data['global-code'] = global_code
        if result and self.data['passed'] <= id:
            self.data['passed'] = id + 1
        cell['code'] = code
        cell['output'] = tornado.escape.xhtml_escape(
            output).replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
        cell['response']['display'] = 'danger' if caught_exception else ('success' if result else 'warning')
        cell['response']['message'] = message
        self.save()
        # return output, result


def slugify(value):
    """
    From django
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)


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


class NotebookHandler(tornado.web.RequestHandler):
    def initialize(self, notebooks, cell_handlers):
        self.notebooks = notebooks
        self.cell_handlers = cell_handlers

    def get(self, slug):
        notebook_file = './Notebooks/'
        try:
            notebook_file += self.notebooks[slug]
        except KeyError:
            try:
                search_for_notebooks(self.notebooks)
                notebook_file += self.notebooks[slug]
            except KeyError:
                print('The file does not exist. There are only ', self.notebooks.keys())
                raise tornado.web.HTTPError(404)
        cell_handler = CellHandler(notebook_file)
        if len(self.cell_handlers):
            self.cell_handlers[0] = cell_handler
        else:
            self.cell_handlers.append(cell_handler)
        self.render("static/notebook.html", home=self.reverse_url('home'))


def make_app():
    notebooks = {}  # Very shady use of references...
    cell_handlers = []
    return tornado.web.Application([
        tornado.web.url(r'/', HomeHandler, dict(notebooks=notebooks), name='home'),
        tornado.web.url(r'/ws', RunWebSocket, dict(cell_handlers=cell_handlers)),
        tornado.web.url(r'/nb/(.*)', NotebookHandler,
                        dict(notebooks=notebooks, cell_handlers=cell_handlers),
                        name='notebook'),
    ], static_path='./static')


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    webbrowser.open('http://localhost:8000/')
    tornado.ioloop.IOLoop.current().start()
