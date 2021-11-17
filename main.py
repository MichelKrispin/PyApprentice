#!/usr/bin/env python3
import yaml
import json
import re
import traceback
import tornado.ioloop
import tornado.web
import tornado.websocket

from io import StringIO
from contextlib import redirect_stdout


class CellHandler:
    def __init__(self):
        with open('demo.yaml', 'r') as f:
            self.data = yaml.safe_load(f)

    def send_as_str(self):
        return json.dumps(self.data)

    def check(self, code, id):
        """Runs the code sandboxed and
        calls the check function with the result.

        Args:
            code ([type]): [description]
            id ([type]): [description]
        """
        scope = {'__name__': '__main__',
                 '__builtins__': globals()['__builtins__']}

        output = ''
        f = StringIO()
        with redirect_stdout(f):
            try:
                exec(code, scope)
            except Exception as e:
                output = traceback.format_exc()
                # Remove the traceback for this file
                # TODO: Fix regex
                output = re.sub(
                    r'  File.+[\r\n]+.+(?=exec\(code, scope\))?',
                    '', output)
        output = f.getvalue() if not output else output
        print(output)
        # Find the checking function and run it in own scope
        check_code = ''
        for cell in self.data['cells']:
            if cell['id'] == id:
                check_code = cell['check']
        check_code += '\nresult = check(_Scope, _Output)'

        check_scope = {'__name__': '__main__',
                       '__builtins__': globals()['__builtins__'],
                       '_Scope': scope, '_Output': output}

        f = StringIO()
        with redirect_stdout(f):
            exec(check_code, check_scope)
        print('------\n', f.getvalue(), '------\n')
        result = check_scope['result']

        for i, cell in enumerate(self.data['cells']):
            if cell['id'] == id:
                self.data['cells'][i]['output'] = tornado.escape.xhtml_escape(
                    output).replace('\n', '<br>').replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')
                self.data['cells'][i]['passed'] = result
        return output, result


cell_handler = CellHandler()


class RunWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message(cell_handler.send_as_str())

    def on_message(self, message):
        data = json.loads(message)
        output, result = cell_handler.check(data['code'], data['id'])
        print(f'f{output} which is {result}')
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
    tornado.ioloop.IOLoop.current().start()
