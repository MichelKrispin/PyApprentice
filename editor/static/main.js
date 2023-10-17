// =====
// Editor settings
// =====

const default_settings = {
  showPrintMargin: false,
  wrap: true,
  theme: 'ace/theme/solarized_dark',
  mode: 'ace/mode/python',
  fontSize: '12pt',
};

// Make the gutter smaller
const smallerGutterRenderer = {
  getWidth: function (session, lastLineNumber, config) {
    return lastLineNumber.toString().length * config.characterWidth - 12;
  },
  getText: function (session, row) {
    return row + 1;
  },
};

function resizeEditor(editor, id, numLines) {
  document.getElementById(id).style.height =
    numLines * editor.renderer.lineHeight + 'px';
  editor.resize();
}

// =====
// Initialize all editors
// =====

// For markdown conversion
const converter = new showdown.Converter({ tables: true });

let editorText = ace.edit('editor-text', {
  ...default_settings,
  mode: 'ace/mode/markdown',
});
editorText.session.gutterRenderer = smallerGutterRenderer;
editorText.setValue('Placeholder!');
resizeEditor(editorText, 'editor-text', 15);
editorText.getSession().on('change', function () {
  document.getElementById('editor-text-output').innerHTML = converter.makeHtml(
    editorText.getSession().getValue()
  );
});

let editorGlobalCode = ace.edit('editor-global-code', default_settings);
editorGlobalCode.session.gutterRenderer = smallerGutterRenderer;
resizeEditor(editorGlobalCode, 'editor-global-code', 15);

let editorCode = ace.edit('editor-code', default_settings);
editorCode.session.gutterRenderer = smallerGutterRenderer;
editorCode.setValue('Placeholder!');
resizeEditor(editorCode, 'editor-code', 15);

let editorCheck = ace.edit('editor-check', default_settings);
editorCheck.session.gutterRenderer = smallerGutterRenderer;
editorCheck.setValue('Placeholder!');
resizeEditor(editorCheck, 'editor-check', 15);

// =====
// Global variables
// =====

let cellData = {};

// =====
// Update UI
// =====

function updateCellSelection() {
  // Inject all cell ids into the select list
  let selectCellHTML = '';
  for (let i = 0; i < cellData.length; i++) {
    selectCellHTML += `<option>${cellData[i]['id']}</option>`;
  }
  document.getElementById('select-cell').innerHTML = selectCellHTML;
}

function saveCurrentCellData() {
  const cellId = document.getElementById('select-cell').value;
  // Save the current data to the cellData
  for (let i = 0; i < cellData.length; i++) {
    if (cellData[i]['id'] == cellId) {
      cellData[i]['text'] = editorText.session.getValue();
      cellData[i]['code'] = editorCode.session.getValue();
      cellData[i]['check'] = editorCheck.session.getValue();
      cellData[i]['title'] = document.getElementById('cell-title').value;
      break;
    }
  }
}

// =====
// On change callback
// =====

// Update the data by requesting all necessary data
async function getNotebookData() {
  const notebook = document.getElementById('select-notebook').value;
  const response = await fetch(
    'notebook?' +
      new URLSearchParams({
        notebook: notebook,
      })
  );
  if (!response.ok) {
    throw new Error('Network response was not OK');
  }
  const data = await response.json();

  // Set the global values
  editorGlobalCode.setValue(data['global-code']);
  document.getElementById('title').value = data['title'];

  // Save the cells
  cellData = data['cells'];

  // Then update the selection list
  updateCellSelection();
  // Then set the cell data once
  changeCell();
}

function changeCell() {
  saveCurrentCellData();

  // Then change the data
  const cellId = document.getElementById('select-cell').value;
  // Get the array with the correct id
  let cell;
  for (let i = 0; i < cellData.length; i++) {
    if (cellData[i]['id'] == cellId) {
      cell = cellData[i];
      break;
    }
  }

  // Set the local cell values
  editorText.setValue(cell['text']);
  editorCode.setValue(cell['code']);
  editorCheck.setValue(cell['check']);
  document.getElementById('cell-title').value = cell['title'];
}

async function updateCell() {
  // Get the information from the fields
  saveCurrentCellData();

  const data = {
    cells: cellData,
    title: document.getElementById('title').value,
    'global-code': editorGlobalCode.session.getValue(),
    passed: 0,
    response: {
      display: 'none',
      message: '',
    },
  };

  // Post them to the server
  const response = await fetch('notebook', {
    method: 'POST',
    cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
    headers: {
      'Content-Type': 'application/json',
    },
    redirect: 'follow',
    referrerPolicy: 'no-referrer',
    body: JSON.stringify(data),
  });

  // Scream if something went wrong
  if (!response.ok) {
    throw new Error('Network response was not OK!');
  }
  const responseStatus = await response.json();
  if (!responseStatus['success']) {
    throw new Error('Network response was not a success!');
  }
}

function deleteCell() {
  console.log('TODO: Delete the cell!');
}

function moveCellRight() {
  const cellId = document.getElementById('select-cell').value;

  // Get adjacent cell
  let higherIndices = [];
  for (let i = 0; i < cellData.length; i++) {
    if (cellData[i]['id'] - cellId > 0) {
      higherIndices.push(i);
    }
  }
  // Check if there actually are higher indices
  if (higherIndices.length < 1) {
    return;
  }
  const nextId = Math.max(...higherIndices);

  // Then swap the indices
  let cellIdIdx;
  let nextIdIdx;
  for (let i = 0; i < cellData.length; i++) {
    if (cellData[i]['id'] == cellId) {
      cellIdIdx = i;
    } else if (cellData[i]['id'] == nextId) {
      nextIdIdx = i;
    }
  }
  cellData[cellIdIdx]['id'] = nextId;
  cellData[nextIdIdx]['id'] = cellId;

  updateCell();
  updateCellSelection();
  document.getElementById('select-cell').value = nextId;
}

function moveCellLeft() {
  const cellId = document.getElementById('select-cell').value;

  // Get adjacent cell
  let lowerIndices = [];
  for (let i = 0; i < cellData.length; i++) {
    if (cellId - cellData[i]['id'] > 0) {
      lowerIndices.push(i);
    }
  }
  // Check if there actually are lower indices
  if (lowerIndices.length < 1) {
    return;
  }
  const previousId = Math.max(...lowerIndices);

  // Then swap the indices
  let cellIdIdx;
  let previousIdIdx;
  for (let i = 0; i < cellData.length; i++) {
    if (cellData[i]['id'] == cellId) {
      cellIdIdx = i;
    } else if (cellData[i]['id'] == previousId) {
      previousIdIdx = i;
    }
  }
  cellData[cellIdIdx]['id'] = previousId;
  cellData[previousIdIdx]['id'] = cellId;

  updateCell();
  updateCellSelection();
  document.getElementById('select-cell').value = previousId;
}

function addCell() {
  // Get highest index
  let indices = [];
  for (let i = 0; i < cellData.length; i++) {
    indices.push(i);
  }
  let newId = 0;
  // Check if there actually are already some indices
  if (indices.length > 0) {
    newId = Math.max(...indices) + 1;
  }
  cellData.push({
    check: '',
    code: '',
    text: '',
    title: '',
    id: newId,
  });

  updateCell();
  updateCellSelection();
  document.getElementById('select-cell').value = newId;
}

// =====
// Initialize
// =====

getNotebookData();

// =====
// Modal for delete cell
// =====

document.addEventListener('DOMContentLoaded', () => {
  // Functions to open and close a modal
  function openModal($el) {
    $el.classList.add('is-active');
  }

  function closeModal($el) {
    $el.classList.remove('is-active');
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

  // Add a click event on buttons to open a specific modal
  (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);

    $trigger.addEventListener('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  (
    document.querySelectorAll(
      '.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button'
    ) || []
  ).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  // Add a keyboard event to close all modals
  document.addEventListener('keydown', (event) => {
    if (event.code === 'Escape') {
      closeAllModals();
    }
  });
});
