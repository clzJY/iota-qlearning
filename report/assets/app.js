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
  if (!target) return;
  let opened = false;
  for (let node = target; node; node = node.parentElement) {
    if (node.tagName === 'DETAILS' && !node.open) { node.open = true; opened = true; }
  }
  if (opened) requestAnimationFrame(() => target.scrollIntoView({ behavior: 'instant' }));
}
window.addEventListener('hashchange', revealEvidence);
revealEvidence();

// Track the section at the top of the reading area, including deep links and
// changing heights when optional evidence is opened. Native links work without JS.
const readingBar = document.getElementById('reading-position');
const readingCurrent = document.getElementById('reading-current');
const readingCaption = document.getElementById('reading-caption');
const readingSubphase = document.getElementById('reading-subphase');
const subsectionLinks = [...document.querySelectorAll('.jump-subsections a')];
const readingSections = [...document.querySelectorAll('[data-reading-title]')];
const readingLinks = [...document.querySelectorAll('.reading-steps a, .report-quick-links a')];
readingBar.hidden = false;
let readingFrame = null;
function updateReadingPosition() {
  readingFrame = null;
  // Allow two pixels for fractional anchor-position rounding.
  const offset = readingBar.getBoundingClientRect().height + 26;
  let current = readingSections[0];
  for (const section of readingSections) {
    if (!section.getClientRects().length) continue;
    if (section.getBoundingClientRect().top <= offset) current = section;
    else break;
  }
  const part = current.dataset.readingPart;
  const context = current.dataset.readingContext;
  readingCaption.textContent = part ? `PART ${part} OF 5` : (current.id === 'reproduce' ? 'SUPPORTING FILES' : 'OVERVIEW');
  readingCurrent.textContent = current.dataset.readingTitle;
  const mainPart = part ? readingSections.find(section => section.dataset.readingPart === part) : current;
  readingCurrent.setAttribute('href', '#' + mainPart.id);
  readingSubphase.textContent = context || current.dataset.readingTitle;
  readingSubphase.setAttribute('href', '#' + current.id);
  for (const link of subsectionLinks) {
    if (link.hash === '#' + current.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
  for (const link of readingLinks) {
    const target = document.getElementById(link.hash.slice(1));
    if (part && target.dataset.readingPart === part) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
}
function scheduleReadingPosition() {
  if (readingFrame === null) readingFrame = requestAnimationFrame(updateReadingPosition);
}
window.addEventListener('scroll', scheduleReadingPosition, { passive: true });
window.addEventListener('resize', scheduleReadingPosition);
window.addEventListener('hashchange', scheduleReadingPosition);
document.addEventListener('toggle', scheduleReadingPosition, true);
const readingResize = new ResizeObserver(() => {
  document.documentElement.style.setProperty('--reading-offset', `${readingBar.getBoundingClientRect().height + 24}px`);
  scheduleReadingPosition();
});
readingResize.observe(readingBar);
readingResize.observe(document.getElementById('main'));
updateReadingPosition();
