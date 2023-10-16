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

let editorCode = ace.edit('editor-code', default_settings);
editorCode.session.gutterRenderer = smallerGutterRenderer;
editorCode.setValue('Placeholder!');
resizeEditor(editorCode, 'editor-code', 15);

let editorCheck = ace.edit('editor-check', default_settings);
editorCheck.session.gutterRenderer = smallerGutterRenderer;
editorCheck.setValue('Placeholder!');
resizeEditor(editorCheck, 'editor-check', 15);

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
  console.log(data);
  // TODO!!
}
