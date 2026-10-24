'use strict';

// The solid robot and dock stay fixed. Only translucent route echoes move.
const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
for (const scene of document.querySelectorAll('.route-scene')) {
  const figure = scene.closest('figure');
  const motionButton = figure.querySelector('.route-motion-button');
  function setRoutePaused(paused) {
    if (paused) scene.pauseAnimations(); else scene.unpauseAnimations();
    figure.classList.toggle('routes-paused', paused);
    motionButton.textContent = paused ? 'Play routes' : 'Pause routes';
    motionButton.setAttribute('aria-pressed', String(paused));
  }
  function applyMotionPreference() {
    setRoutePaused(motionPreference.matches);
    motionButton.hidden = motionPreference.matches;
  }
  motionButton.addEventListener('click', () => setRoutePaused(!scene.animationsPaused()));
  motionPreference.addEventListener('change', applyMotionPreference);
  applyMotionPreference();
}

// Values below are saved experimental checkpoints, not a live training run.
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

function revealEvidence() {
  const target = document.getElementById(location.hash.slice(1));
  if (target && target.matches('details.extension-details')) target.open = true;
}
window.addEventListener('hashchange', revealEvidence);
revealEvidence();
