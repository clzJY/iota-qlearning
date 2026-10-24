'use strict';

// This calculator is illustrative. Experimental values are loaded below from
// embedded, saved checkpoints; no live training or external request is involved.
const form = document.getElementById('update-form');
function calculateUpdate() {
  const ids = ['old-q', 'next-q', 'alpha', 'gamma'];
  const [oldQ, nextQ, alpha, gamma] = ids.map(id => {
    const value = Number(document.getElementById(id).value);
    document.getElementById(`${id}-label`).textContent = value.toFixed(2);
    return value;
  });
  const terminal = document.getElementById('transition').value === 'terminal';
  const target = terminal ? 1 : gamma * nextQ;
  document.getElementById('next-q').disabled = terminal;
  document.getElementById('calc-detail').textContent =
    `${oldQ.toFixed(3)} + ${alpha.toFixed(2)} × (${target.toFixed(3)} − ${oldQ.toFixed(3)})`;
  document.getElementById('calc-value').textContent = (oldQ + alpha * (target - oldQ)).toFixed(3);
}
form.addEventListener('input', calculateUpdate);
form.addEventListener('change', calculateUpdate);
form.addEventListener('submit', event => event.preventDefault());
calculateUpdate();

const saved = JSON.parse(document.getElementById('experiment-data').textContent);
const caseSelect = document.getElementById('snapshot-case');
const episodeSelect = document.getElementById('snapshot-episode');

function drawSnapshot() {
  const data = saved[caseSelect.value];
  const episode = episodeSelect.value;
  const values = data.snapshots[episode];
  const table = document.createElement('table');
  table.className = 'q-table';
  const caption = document.createElement('caption');
  caption.textContent = `${data.start} → ${data.goal}, seed 0, after episode ${episode}. Actions name destinations; — means unavailable.`;
  caption.className = 'small';
  table.append(caption);
  const head = table.createTHead().insertRow();
  for (const text of ['s / a', ...data.states]) {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = text;
    head.append(th);
  }
  const body = table.createTBody();
  data.states.forEach((state, i) => {
    const row = body.insertRow();
    const label = document.createElement('th');
    label.scope = 'row';
    label.textContent = state;
    row.append(label);
    data.states.forEach((_, j) => {
      const cell = row.insertCell();
      const value = values[i][j];
      if (value === null) {
        cell.textContent = '—';
        cell.className = 'unavailable';
      } else {
        cell.textContent = value.toFixed(4);
        cell.style.backgroundColor = `rgba(22,123,112,${0.05 + value * 0.3})`;
      }
    });
  });
  document.getElementById('snapshot-table').replaceChildren(table);
}
function changeCase() {
  episodeSelect.replaceChildren();
  Object.keys(saved[caseSelect.value].snapshots).map(Number).sort((a, b) => a - b).forEach(episode => {
    const option = document.createElement('option');
    option.value = String(episode);
    option.textContent = episode.toLocaleString('en-US');
    episodeSelect.append(option);
  });
  drawSnapshot();
}
caseSelect.addEventListener('change', changeCase);
episodeSelect.addEventListener('change', drawSnapshot);
changeCase();
