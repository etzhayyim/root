const statusEl = document.getElementById('status');

function render(pending) {
  if (pending) {
    statusEl.classList.remove('empty');
    statusEl.innerHTML = `Next MF download → <b>mf-ingest/${pending}</b>`;
  } else {
    statusEl.classList.add('empty');
    statusEl.textContent = 'No pending download — pick a target first.';
  }
}

function refresh() {
  chrome.runtime.sendMessage({ type: 'getPending' }, (resp) => {
    render(resp?.pending ?? null);
  });
}

document.querySelectorAll('button.pick').forEach((btn) => {
  btn.addEventListener('click', () => {
    const name = btn.dataset.name;
    chrome.runtime.sendMessage({ type: 'setNext', filename: name }, () => refresh());
  });
});

document.getElementById('clear').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'clear' }, () => refresh());
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type === 'captured') {
    statusEl.classList.remove('empty');
    statusEl.innerHTML = `Captured <b>${msg.filename}</b> — pick next target or close.`;
  }
});

refresh();
