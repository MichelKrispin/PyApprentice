#!/usr/bin/env python3
import os
import yaml
import PySimpleGUI as sg

from shutil import copyfile


# -----------------------
# YAML For nice printing
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


# -----------------------

def save_data(d, v, file_name, cell_id, close=False):
    update_data(d, v, cell_id)
    copyfile(file_name, file_name + '.backup')
    with open(file_name, 'w') as f:
        yaml.dump(d, f, default_flow_style=False)
    if close:
        os.remove(file_name + '.backup')


def load_data(file_name):
    with open(file_name, 'r') as f:
        loaded = yaml.safe_load(f)
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
        print(f'{i} does not exist. Highest is {get_highest_id(d)}')
        return
    w['max-id'].update(f'Max ID: {get_highest_id(data)}')
    w['code'].update(cell['code'])
    w['text'].update(cell['text'])
    w['check'].update(cell['check'])
    w['title'].update(cell['title'])


if __name__ == '__main__':
    file = './Notebooks/beginner.yaml'
    data = load_data(file)

    sg.theme('DarkTeal11')
    layout = [[sg.Text(f'Max ID: {get_highest_id(data)}', key='max-id'),
               sg.InputText('0', size=(56, 5), key='id'),
               sg.Button('Update ID'), sg.Button('Add Field')],
              [sg.HorizontalSeparator()],

              [sg.Text('Title'), sg.InputText(key='title')],
              [sg.HorizontalSeparator()],

              [sg.Text('Text')],
              [sg.Multiline(size=(100, 10), key='text')],
              [sg.HorizontalSeparator()],

              [sg.Text('Code')],
              [sg.Multiline(size=(100, 10), key='code')],

              [sg.HorizontalSeparator()],

              [sg.Text('Check')],
              [sg.Multiline(size=(100, 10), key='check')],

              [sg.HorizontalSeparator()],
              [sg.Button('Save'), sg.Button('Quit')]]

    # Create the Window
    window = sg.Window('PyApprentice Editor', layout, font=('Courier', 14), element_justification='c').Finalize()
    update_display(data, window, 0)

    # Event loop
    last_id = 0
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Quit':
            save_data(data, values, file, close=True)
            break
        if event == 'Save':
            save_data(data, values, file, last_id)
        elif event == 'Update ID':
            save_data(data, values, file, last_id)
            try:
                i = int(values['id'])
            except ValueError:
                print('ID field has to be an integer value')
                continue
            update_display(data, window, i)
        elif event == 'Add Field':
            i = get_highest_id(data)
            data['cells'].append({
                'check': """ 
def check(scope, output):
    if "" in output:
        return True, 'Wundervoll.'
    elif 'Traceback' in output:
        return False, 'Exception'
    else:
        return False, 'Und so sieht es aus, wenn es noch nicht ganz richtig ist.'""",
                'code': """
# Python Code
print('Hello')
                """,
                'id': i + 1,
                'output': '',
                'response': {
                    'display': 'none',
                    'message': ''
                },
                'text': 'Description of current cell',
                'title': 'Hello',
            })
            last_id = i + 1
            window['id'].update(f'{last_id}')
            update_display(data, window, last_id)

    window.close()
