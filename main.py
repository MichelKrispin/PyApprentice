#!/usr/bin/env python3
import yaml
import json

import traceback
import tornado.ioloop
import tornado.web
import tornado.websocket

from shutil import copyfile
from io import StringIO
from contextlib import redirect_stdout


class CellHandler:
    def __init__(self):
        self.file_name = 'Notebooks/beginner_.yaml'
        with open(self.file_name, 'r') as f:
            self.data = yaml.safe_load(f)

    def send_as_str(self):
        return json.dumps(self.data)

    def save(self):
        """Save the data to file."""
        copyfile(self.file_name, self.file_name + '.backup')
        with open(self.file_name, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)

    def check(self, global_code, code, id):
        """Runs the code sandboxed and
        calls the check function with the result.

        Args:
            code ([type]): [description]
            id ([type]): [description]
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
        if global_code != '':
            f = StringIO()
            with redirect_stdout(f):
                try:
                    exec(global_code, scope)
                except Exception as e:
                    exception = traceback.format_exc()
                    # Remove the traceback for this file
                    lines = exception.split('\n')
                    exercise_name = cell['title']
                    output = '\n'.join([lines[0]] + lines[3:]) \
                        .replace('<astring>', 'Global Code')
            caught_exception = output != ''
            output = output if caught_exception else f.getvalue()

            # If everything went right do a little bit of reflection magic
            # such that every function created in the global functions scope
            # knows that.
            for attr in scope:
                try:
                    if scope[attr].__code__.co_filename == '<string>':
                        scope[attr].__code__ = scope[attr].__code__.replace(co_filename='global_functions.py')
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
                        .replace('<astring>', exercise_name)
            caught_exception = output != ''
            output = output if caught_exception else f.getvalue()

            # Find the checking function
            check_code = cell['check']
            check_code += '\nresult = check(_Scope, _Output)'

            check_scope = {'__name__': '__main__',
                           '__builtins__': globals()['__builtins__'],
                           '_Scope': scope, '_Output': output}

            # Run the checking function in the created scope
            f = StringIO()
            with redirect_stdout(f):
                exec(check_code, check_scope)
            # print('------\n', f.getvalue(), '------\n')
            result = check_scope['result']

        # Save data
        self.data['global-code'] = global_code
        if result and self.data['passed'] <= id:
            self.data['passed'] = id + 1
        cell['code'] = code
        cell['output'] = tornado.escape.xhtml_escape(
            output).replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
        cell['response'] = 'danger' if caught_exception else ('success' if result else 'warning')
        self.save()
        return output, result


cell_handler = CellHandler()


class RunWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message(cell_handler.send_as_str())

    def on_message(self, message):
        data = json.loads(message)
        output, result = cell_handler.check(data['global-code'], data['code'], data['id'])
        # print(f'{output}which is {result}\n')
        self.write_message(cell_handler.send_as_str())

    def on_close(self):
        print("WebSocket closed")


def make_app():
    return tornado.web.Application([
        (r'/ws', RunWebSocket),
        (r'/(.*)', tornado.web.StaticFileHandler,
         {'path': './static', 'default_filename': 'index.html'}),
    ], static_path='./static')


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    print(f'Running PyApprentrice on http://localhost:8000/\n')
    tornado.ioloop.IOLoop.current().start()
