/* Initialize the global editor. */
const default_settings = {
    showPrintMargin: false,
    wrap: true,
    theme: 'ace/theme/solarized_dark',
    mode: 'ace/mode/python',
    fontSize: '16pt',
};

// Make the gutter smaller
const smallerGutterRenderer = {
    getWidth: function (session, lastLineNumber, config) {
        return lastLineNumber.toString().length * config.characterWidth - 12;
    },
    getText: function (session, row) {
        return row + 1;
    }
};


let editors = {
    'global-editor': ace.edit('global-editor', default_settings),
};
editors['global-editor'].session.gutterRenderer = smallerGutterRenderer

function resizeEditor(id, numLines) {
    document.getElementById(id).style.height =
        numLines * editor.renderer.lineHeight + 'px';
    editors[id].resize();
}

/* Check for the WebSocket connection and act appropiately. */
let ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = function () {
    // ws.send('Hello, world');
};
ws.onmessage = function (evt) {
    data = JSON.parse(evt.data);
    editors['global-editor'].setValue(data['global-code']);
    document.getElementById('title').innerHTML = data['title'];
    cells_html = Array.from(' '.repeat(data['cells'].length));
    data['cells'].forEach((cell) => {
        cells_html[cell['id']] = `
        <div class="box">
          <div class="columns is-vcentered">
            <div class="column">
              <p class="title is-4">${cell['title']}</p>
            </div>
            <div class="column">
              <button
                class="button is-primary is-pulled-right"
                onclick="runCell(${cell['id']})"
              >
                <span>Run</span>
                <span class="icon is-small">
                  <i class="fas fa-play"></i>
                </span>
              </button>
            </div>
          </div>
          <div class="block">
          ${cell['text']}
          </div>
          <div class="editor" id="editor-${cell['id']}"></div>
      `;
        if (cell['output']) {
            cells_html[cell['id']] += `
            <article class="message">
              <div class="message-body" style="font-family: monospace">
                <p>
                  ${cell['output']}
                </p>
              </div>
            </article>
        `;
        }
        cells_html[cell['id']] += '</div>';
    });
    document.getElementById('tasks').innerHTML = cells_html.join('\n');
    data['cells'].forEach((cell) => {
        let editor = ace.edit(`editor-${cell['id']}`, default_settings);
        editor.session.gutterRenderer = smallerGutterRenderer;
        editor.setValue(cell['code']);
        editors[`editor-${cell['id']}`] = editor;
    });
};

function runCell(id) {
    console.log();
    ws.send(
        JSON.stringify({
            id: id,
            'global-code': editors['global-editor'].getValue(),
            code: editors[`editor-${id}`].getValue(),
        })
    );
}
