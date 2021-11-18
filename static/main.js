/* Initialize the global editor. */
const default_settings = {
    showPrintMargin: false,
    wrap: true,
    theme: 'ace/theme/solarized_dark',
    mode: 'ace/mode/python',
    fontSize: '14pt',
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

function resizeEditor(editor, id, numLines) {
    document.getElementById(id).style.height =
        numLines * editor.renderer.lineHeight + 'px';
    editor.resize();
}

// For markdown conversion
const converter = new showdown.Converter({'tables': true});

/* Check for the WebSocket connection and act appropiately. */
let ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = function () {
    console.log('PyApprentice successfully connected.\n\n\t🎉 Have fun 🎉\n\n');
};
ws.onmessage = function (evt) {
    data = JSON.parse(evt.data);
    editors['global-editor'].setValue(data['global-code']);
    document.getElementById('title').innerHTML = data['title'];
    cells_html = Array.from(' '.repeat(data['cells'].length));
    data['cells'].forEach((cell) => {
        if (cell['id'] <= data['passed']) {
            cells_html[cell['id']] = `
            <div class="box content">
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
              ${converter.makeHtml(cell['text'])}
              </div>
              <div class="editor" id="editor-${cell['id']}"></div>
          `;
            cells_html[cell['id']] += `
                <article class="message is-${cell['response']}">
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
        if (cell['id'] <= data['passed']) {
            let editor = ace.edit(`editor-${cell['id']}`, default_settings);
            editor.session.gutterRenderer = smallerGutterRenderer;
            editor.commands.addCommand({
                name: "sendCell",
                bindKey: {win: "Ctrl-Enter"},
                exec: function (editor) {
                    runCell(cell['id']);
                }
            });
            editor.setValue(cell['code']);
            resizeEditor(editor, `editor-${cell['id']}`, 10);
            editors[`editor-${cell['id']}`] = editor;
        }
    });

    // After updating everything set the css classes to header
    ['h2', 'h3', 'h4', 'h5'].forEach((h) => {
        const elements = document.getElementsByTagName(h);
        for (let i = 0; i < elements.length; i++) {
            const el = elements[i];
            el.setAttribute('class', 'title is-' + (parseInt(h[1]) + 3));
        }
    })

};

function runCell(id) {
    ws.send(
        JSON.stringify({
            id: id,
            'global-code': editors['global-editor'].getValue(),
            code: editors[`editor-${id}`].getValue(),
        })
    );
}
