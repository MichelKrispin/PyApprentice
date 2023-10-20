# PyApprentice

A project with interactive notebooks for solving pre-defined tasks.

It is based on the idea of notebooks, but here, each cell has its individual scope and is evaluated on its own.
The resulting scope of this cell as well as the output can then be checked for something that should be there and tell the user whether the task was successfully solved.
Every cell can make use of globally defined functions, which get injected into the scope of every cell beforehand.

> [!WARNING]
> Arbitrary code can be executed, so this project should not be run on a public server!

## Starting

Install all dependencies preferably in a virtual environment (`pip install -r requirements.txt`).
Then, run the `main.py` script to start the server.

```python
python main.py
```

This should open the browser (if not, its at _http://localhost:8000/_) and show you all found notebooks.
These Notebooks should be in a directory called 'Notebooks', relative to the working directory.
By default, the notebooks that will be edited are in the path above the `editor.py` file.
If you want to change that, run the path as the first command line argument such as `python ../main.py ../Notebooks`.

## Usage

The global code will be used in all cells, other than that each cell has its own scope and will be run individually.
You can use `Ctrl`+`Enter` to run a cell instead of clicking on the `Run` button.

The changes will be saved automatically, but the original version of the file is saved.
If you want to revert all changes you made, delete the normal `notebook.json` file and remove the `.original` from the name of the other.

## Editor

You can edit any Notebook by opening the editor.
Go into the `editor` directory and start it.

```python
python editor.py
```

This should open the browser (if not, its at _http://localhost:8001/_).
By default, the notebooks that will be edited are in the path above the `editor.py` file.
If you want to change that, run the path as the first command line argument such as `python editor/editor.py Notebooks`.

Most of the editor is self-explanatory.
The `Code` is what will be inside the code field when starting up.

The `Check` field is the field where you enter valid (!) python code which will be also be injected into each cell.
This function will then be called after running the cell's code and should always have the following form

```python
def _Check(scope: dict[str, Any], output: str) -> Tuple[Bool, str]:
    """Check the scope and the output of the cell for the given task.
    The scope has the names of all variables as well as their value.
    The output is whatever went to the output, stdout as well as stderr.
    After doing some task specific checking, the function should return
    whether the cell passes the task (True, False) and then a message
    that will be printed.

    Args:
        scope (dict[str, Any]): The scope of the cell. E.g., a = 2 -> scope['a'] = 2.
        output (str): The output of the string including Tracebacks or print results.

    Returns:
        Tuple[Bool, str]: Whether the cell passed and the message that will be printed accordingly.
    """
    return True, ""
```

Note that the program itself shouldn't be open while editing as it will have a backup and overwrites any changes.
So, go to the home page, edit, check.

### Format

The format can be ignored if the editor is used but if there is the need to edit a Notebook by hand, then the following might be interesting.
Each Notebook has the following structure:
```json
{
  "cells": [{...}, ...],
  "title": "Title",
  "global-code": "# Some python code\nprint('abc')",
  "passed": 0
}
```
The `title` is the main title that will be displyed at the top, the `global-code` is whatever is in the global code field from the very start.
`passed` is used to count how many cells have already been successfully passed.
At the beginning it should be set to `0` to display only the first cell, and these numbers are directly translated to the cell ids, which are explained later.
So, if `passed` equals to, let's say, `5`, then all cells whose ids are less or equal to `5` will be displayed.

Each cell then looks like this:
```json
{
  "title": "Cell title",
  "text": "Markdown description for this cell",
  "code": "# Prefilled python code\nprint('Hello')",
  "check": "def _Check(scope, output):\n    return True, 'Passed'",
  "id": 0,
  "output": "Hello\n",
  "response": {
      "display": "success",
      "message": "Passed"
  },
}
```
The `title` is the cell title, while `text` is the markdown description that will be displayed on the top of the cell.
The `code` is whatever will sit in the code field on startup and the `check` function is the python code that will check the code for passing.
The `id` is the unique id of this cell and should be incremented for each cell, so this one is the first, the next one should have `"id": 1` and so on. 
The `output` and the `response` should only be filled by the server because the former is the output of the code while the latter is the second return value of the `_Check` function (in this example 'Passed').
The `response["display"]` informs about how the output will be shown.
At the beginning it should be `"display": "none"` (and `"message": ""`) as the cell wasn't run yet.
Then, if the `_Check` function returned `True`, it will have the form `"display": "success"` which will show it green, if the check function returned `False`, then depending on whether an exception was caught, it has the form `"display": "warning"` or `"display": "error"`.
But again, these values shouldn't be set by hand.
