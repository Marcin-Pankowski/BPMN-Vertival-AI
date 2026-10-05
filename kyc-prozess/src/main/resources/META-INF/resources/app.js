/* KYC-Prüfprozess: Webinterface (Antrag prüfen, manuelle Prüfung, Dashboard).
 * Bezeichner englisch, Oberfläche deutsch. Antragsfelder folgen dem Datensatzschema (deutsch). */
'use strict';

const REVIEW_GROUP = 'kyc-reviewers';
const REFRESH_MS = 2000;

// Spiegel der DMN-Tabelle KYC_RuleCheck für die Anzeige; ausgewertet wird ausschließlich im DMN.
const RULES = {
  R1: { label: 'Kunde nicht selbst wirtschaftlich berechtigt', condition: 'wirtschaftlich berechtigt = Nein',
    value: app => getPath(app, ['kunde', 'ist_selbst_wirtschaftlich_berechtigt']) },
  R2: { label: 'PEP-Status bestätigt', condition: 'PEP = Ja', value: app => getPath(app, ['screening', 'pep']) },
  R3: { label: 'Möglicher Screening-Treffer ungeklärt', condition: 'Sanktionsscreening = möglicher Treffer, ungeklärt',
    value: app => getPath(app, ['screening', 'sanktionsscreening_status']) },
  R4: { label: 'USA-Bezug', condition: 'US-Steuerpflicht, FATCA-US-Person, US-Staatsangehörigkeit, Ansässigkeit oder Adresse USA',
    value: app => usIndicators(app).join(', ') || 'keiner' },
  R5: { label: 'Bestätigter Sanktionstreffer (Ablehnung)', condition: 'Sanktionsscreening = bestätigter Treffer',
    value: app => getPath(app, ['screening', 'sanktionsscreening_status']) },
};

function usIndicators(app) {
  if (!app) return [];
  const tax = app.steuerangaben || {};
  const person = app.kunde || {};
  const found = [];
  if (tax.us_steuerpflicht_laut_selbstauskunft === 'Ja') found.push('US-Steuerpflicht');
  if (tax.fatca_us_person_laut_selbstauskunft === 'Ja') found.push('FATCA');
  if ((person.staatsangehoerigkeiten || []).includes('US')) found.push('Staatsangehörigkeit');
  if ((tax.steuerliche_ansaessigkeit_laut_selbstauskunft || []).includes('US')) found.push('Ansässigkeit');
  if (person.adresse?.land === 'US') found.push('Wohnadresse');
  if ((person.auslandsadressen || []).some(a => a.land === 'US')) found.push('Auslandsadresse');
  return found;
}

const DECISIONS = {
  keine_manuelle_pruefung: { label: 'Keine manuelle Prüfung', tone: 'ok' },
  manuelle_pruefung: { label: 'Manuelle Prüfung', tone: 'warn' },
  unklar: { label: 'Unklar', tone: 'warn' },
  fehler: { label: 'Technischer Fehler', tone: 'bad' },
};

const FIELD_LABELS = {
  prozessphase: 'Prozessphase', identitaetspruefung: 'Identitätsprüfung', status: 'Status', datum: 'Datum', verfahren: 'Verfahren',
  kunde: 'Kunde', vorname: 'Vorname', nachname: 'Nachname', geburtsdatum: 'Geburtsdatum', staatsangehoerigkeiten: 'Staatsangehörigkeiten',
  adresse: 'Wohnadresse', plz: 'PLZ', strasse: 'Straße', hausnummer: 'Hausnummer', ort: 'Ort', land: 'Land',
  ist_selbst_wirtschaftlich_berechtigt: 'Selbst wirtschaftlich berechtigt', auslandswohnsitz: 'Auslandswohnsitz', auslandsadressen: 'Auslandsadressen',
  beschaeftigung: 'Beschäftigung', beruf: 'Beruf', nettoeinkommen_monat_eur_laut_kunde: 'Netto/Monat (EUR)', arbeitgeber: 'Arbeitgeber', name: 'Name',
  entstehung_gesamtvermoegen_freitext: 'Entstehung des Gesamtvermögens',
  mittelherkunft: 'Mittelherkunft', kategorie: 'Kategorie', beschreibung_freitext: 'Beschreibung', geplante_ersteinzahlung_eur: 'Ersteinzahlung (EUR)',
  steuerangaben: 'Steuerangaben', us_steuerpflicht_laut_selbstauskunft: 'US-steuerpflichtig', fatca_us_person_laut_selbstauskunft: 'FATCA-US-Person',
  steuerliche_ansaessigkeit_laut_selbstauskunft: 'Steuerliche Ansässigkeit', erlaeuterung_freitext: 'Erläuterung', selbstauskunft_vorhanden: 'Selbstauskunft vorhanden',
  screening: 'Screening', pep: 'PEP', pep_erlaeuterung: 'PEP-Erläuterung', sanktionsscreening_status: 'Sanktionsscreening', screening_erlaeuterung: 'Screening-Erläuterung',
  kontoantrag: 'Kontoantrag', kontotyp: 'Kontotyp', kontozweck: 'Kontozweck', geplante_nutzung_freitext: 'Geplante Nutzung',
  eingereichte_unterlagen: 'Eingereichte Unterlagen', dokument_id: 'Dokument-ID', typ: 'Typ', textauszug: 'Textauszug',
};

const YES_NO = ['Ja', 'Nein'];
const ENUMS = {
  'kunde.ist_selbst_wirtschaftlich_berechtigt': YES_NO,
  'kunde.auslandswohnsitz': YES_NO,
  'steuerangaben.us_steuerpflicht_laut_selbstauskunft': YES_NO,
  'steuerangaben.fatca_us_person_laut_selbstauskunft': YES_NO,
  'screening.pep': YES_NO,
  'screening.sanktionsscreening_status': ['kein_treffer', 'moeglicher_treffer_ungeklaert', 'bestaetigter_treffer'],
  'beschaeftigung.status': ['angestellt', 'selbststaendig', 'ruhestand', 'oeffentliche_funktion'],
  'mittelherkunft.kategorie': ['Gehaltsersparnisse', 'Ruecklagen_aus_Selbststaendigkeit', 'Schenkung', 'Fahrzeugverkauf', 'Erbschaft', 'Privates_Darlehen'],
  'eingereichte_unterlagen[].typ': ['Arbeitgeberbestaetigung', 'Aktuelle_Arbeitgeberbestaetigung', 'Kaufvertrag', 'Nachlassunterlage', 'Schenkungserklaerung',
    'Finanzierungsvereinbarung', 'Vermoegensaufstellung', 'Ruecklagenbestaetigung', 'Wohnsitz_Selbsterklaerung'],
};

const SECTIONS = [
  { title: 'Kunde', keys: ['kunde'] },
  { title: 'Beschäftigung', keys: ['beschaeftigung'] },
  { title: 'Vermögen und Mittelherkunft', keys: ['entstehung_gesamtvermoegen_freitext', 'mittelherkunft'] },
  { title: 'Steuerangaben', keys: ['steuerangaben'] },
  { title: 'Screening', keys: ['screening'] },
  { title: 'Kontoantrag', keys: ['kontoantrag'] },
  { title: 'Eingereichte Unterlagen', keys: ['eingereichte_unterlagen'] },
  { title: 'Identitätsprüfung (Voraussetzung, kein Modellmerkmal)', keys: ['prozessphase', 'identitaetspruefung'], collapsed: true },
];

const ITEM_TEMPLATES = {
  'kunde.auslandsadressen': () => ({ plz: '', strasse: '', hausnummer: '', ort: '', land: '' }),
  'eingereichte_unterlagen': list => ({ dokument_id: `DOC-${String(list.length + 1).padStart(2, '0')}`, typ: 'Arbeitgeberbestaetigung', textauszug: '' }),
};
const EMPLOYER_TEMPLATE = () => ({ name: '', plz: '', strasse: '', hausnummer: '', ort: '', land: 'DE' });

const NODE_LABELS = { Gateway_Join_Approve: 'Zusammenführung Freigabe', Gateway_Join_Reject: 'Zusammenführung Ablehnung', Gateway_Join_Manual: 'Zusammenführung Prüfung' };

const state = {
  cases: [],
  application: null,
  selectedTaskId: null,
  selectedInstanceId: null,
  viewer: null,
  diagramReady: null,
  markers: [],
  lastDetailKey: null,
};

/* ---------- Hilfsfunktionen ---------- */

const $ = sel => document.querySelector(sel);

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status}: ${text.slice(0, 300)}`);
  }
  const type = response.headers.get('content-type') || '';
  return type.includes('json') ? response.json() : response.text();
}

function label(key) {
  return FIELD_LABELS[key] || key.replace(/_/g, ' ');
}

function formatTime(iso) {
  if (!iso) return '–';
  const d = new Date(iso);
  return d.toLocaleTimeString('de-DE') + '.' + String(d.getMilliseconds()).padStart(3, '0');
}

function formatDuration(fromIso, toIso) {
  if (!fromIso || !toIso) return '';
  const ms = new Date(toIso) - new Date(fromIso);
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

function getPath(obj, path) {
  return path.reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

function decisionBadge(decision) {
  const d = DECISIONS[decision] || { label: decision || '–', tone: '' };
  return `<span class="badge ${d.tone}">${esc(d.label)}</span>`;
}

function ruleBadge(ruleResult, rules) {
  if (!ruleResult) return '<span class="badge">–</span>';
  if (ruleResult === 'green') return '<span class="badge ok">Regeln grün</span>';
  if (ruleResult === 'reject') return `<span class="badge bad">Ablehnung ${esc((rules || []).join(', '))}</span>`;
  return `<span class="badge warn">Prüfbedarf ${esc((rules || []).join(', '))}</span>`;
}

function outcomeOf(instance) {
  if (instance.outcome === 'approved') return { text: 'Freigegeben', tone: 'ok' };
  if (instance.outcome === 'rejected') return { text: 'Abgelehnt', tone: 'bad' };
  if (instance.status === 'error') return { text: 'Fehler', tone: 'bad' };
  if (instance.status === 'active') return { text: instance.waitingAt ? `wartet: ${instance.waitingAt}` : 'aktiv', tone: 'warn' };
  return { text: instance.status, tone: '' };
}

/* ---------- Gemeinsame Bausteine: Regeln und Laya ---------- */

function rulesTable(application, triggered) {
  const hits = new Set(triggered || []);
  const rows = Object.entries(RULES).map(([id, rule]) => `
    <tr class="${hits.has(id) ? 'hit' : ''}">
      <td>${id}</td>
      <td><span class="rule-label">${esc(rule.label)}</span><span class="rule-condition">${esc(rule.condition)}</span></td>
      <td>${esc(rule.value(application) ?? '–')}</td>
      <td>${hits.has(id) ? '✓' : '–'}</td>
    </tr>`).join('');
  return `<table class="rules"><thead><tr><th>Regel</th><th>Bedingung (DMN, COLLECT)</th><th>Wert im Antrag</th><th>Treffer</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function llmBars(llm) {
  if (!llm) return '<p class="note">Noch keine LLM-Bewertung.</p>';
  if (llm.decision === 'fehler') {
    return `<p class="error">${esc(llm.error || 'Laya-Dienst nicht nutzbar')}</p><p class="note">Technischer Fehler → manuelle Prüfung.</p>`;
  }
  const probs = llm.probabilities || {};
  const bars = Object.keys(DECISIONS).filter(k => k in probs).map(key => {
    const p = probs[key] || 0;
    return `<div class="bar ${key === llm.decision ? 'chosen' : ''}">
      <span class="bar-label">${esc(DECISIONS[key].label)}</span>
      <span class="bar-track"><span class="bar-fill ${key}" style="width:${(p * 100).toFixed(1)}%"></span></span>
      <span class="bar-value">${(p * 100).toFixed(1)} %</span></div>`;
  }).join('');
  return `<div class="bars">${bars}</div>
    <p class="note">Modell <code>${esc(llm.model || '–')}</code>. Die Wahrscheinlichkeiten sind nicht kalibriert; Laya liefert keine Begründung.</p>`;
}

function applicationSummary(app) {
  if (!app) return '';
  const k = app.kunde || {};
  const b = app.beschaeftigung || {};
  const m = app.mittelherkunft || {};
  const ko = app.kontoantrag || {};
  const docs = (app.eingereichte_unterlagen || []).map(d => `${d.typ}: ${d.textauszug}`).join(' | ') || 'keine';
  const rows = [
    ['Kunde', `${k.vorname || ''} ${k.nachname || ''}, geb. ${k.geburtsdatum || '–'}`],
    ['Adresse', [k.adresse?.strasse, k.adresse?.hausnummer, k.adresse?.plz, k.adresse?.ort].filter(Boolean).join(' ')],
    ['Beschäftigung', `${b.beruf || '–'} (${b.status || '–'}), ${b.nettoeinkommen_monat_eur_laut_kunde ?? '–'} EUR netto`],
    ['Vermögen', app.entstehung_gesamtvermoegen_freitext],
    ['Mittelherkunft', `${m.kategorie || '–'}: ${m.beschreibung_freitext || ''}`],
    ['Kontoantrag', `${ko.kontotyp || '–'}; Zweck: ${ko.kontozweck || '–'}`],
    ['Geplante Nutzung', ko.geplante_nutzung_freitext],
    ['Unterlagen', docs],
  ];
  return `<table class="kv">${rows.map(([key, value]) => `<tr><td>${esc(key)}</td><td>${esc(value)}</td></tr>`).join('')}</table>`;
}

/* ---------- Ansicht: Antrag prüfen ---------- */

async function loadCases() {
  const data = await api('data/demo_cases.json');
  state.cases = data.kunden;
  const select = $('#case-select');
  select.innerHTML = state.cases.map((c, i) =>
    `<option value="${i}">${esc(c.kunden_id)} – ${esc(c.eingabe.kunde.vorname)} ${esc(c.eingabe.kunde.nachname)}</option>`).join('');
  select.addEventListener('change', () => selectCase(Number(select.value)));
  selectCase(0);
}

function selectCase(index) {
  const chosen = state.cases[index];
  const application = structuredClone(chosen.eingabe);
  delete application.regelpruefung;
  state.application = application;
  $('#case-hint').innerHTML = `Erwarteter Pfad laut Planung: <strong>${esc(chosen.expected_path)}</strong>`;
  renderForm();
  syncJson();
}

function setValue(path, value) {
  let target = state.application;
  for (const key of path.slice(0, -1)) target = target[key];
  target[path[path.length - 1]] = value;
  syncJson();
}

function schemaKey(path) {
  return path.map(p => (typeof p === 'number' ? '[]' : p)).join('.').replace(/\.\[\]/g, '[]');
}

function renderForm() {
  const form = $('#application-form');
  form.innerHTML = '';
  for (const section of SECTIONS) {
    const fieldset = document.createElement('fieldset');
    if (section.collapsed) fieldset.classList.add('collapsed');
    const legend = document.createElement('legend');
    legend.textContent = section.title;
    if (section.collapsed) {
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'ghost small';
      toggle.textContent = 'anzeigen';
      toggle.addEventListener('click', () => {
        fieldset.classList.toggle('collapsed');
        toggle.textContent = fieldset.classList.contains('collapsed') ? 'anzeigen' : 'ausblenden';
      });
      legend.appendChild(toggle);
    }
    fieldset.appendChild(legend);
    const grid = document.createElement('div');
    grid.className = 'grid';
    for (const key of section.keys) {
      if (key in state.application) renderNode(grid, state.application[key], [key]);
    }
    fieldset.appendChild(grid);
    form.appendChild(fieldset);
  }
}

function renderNode(container, value, path) {
  const key = path[path.length - 1];
  const sKey = schemaKey(path);
  if (key === 'arbeitgeber') return renderEmployer(container, value, path);
  if (Array.isArray(value) && (value.length === 0 ? sKey in ITEM_TEMPLATES : typeof value[0] === 'object')) {
    return renderObjectList(container, value, path);
  }
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    const group = document.createElement('div');
    group.className = 'subgroup';
    if (path.length > 1) group.innerHTML = `<div class="subgroup-head">${esc(label(key))}</div>`;
    const grid = document.createElement('div');
    grid.className = 'grid';
    for (const [childKey, childValue] of Object.entries(value)) renderNode(grid, childValue, [...path, childKey]);
    group.appendChild(grid);
    container.appendChild(path.length > 1 ? group : grid.children.length ? fragmentOf(grid) : group);
    return;
  }
  container.appendChild(renderInput(value, path));
}

function fragmentOf(grid) {
  const fragment = document.createDocumentFragment();
  while (grid.firstChild) fragment.appendChild(grid.firstChild);
  return fragment;
}

function renderInput(value, path) {
  const key = path[path.length - 1];
  const sKey = schemaKey(path);
  const wrapper = document.createElement('label');
  wrapper.className = 'field';
  wrapper.innerHTML = `<span>${esc(label(typeof key === 'number' ? path[path.length - 2] : key))}</span>`;
  let input;
  if (ENUMS[sKey]) {
    input = document.createElement('select');
    const options = ENUMS[sKey].includes(value) ? ENUMS[sKey] : [value, ...ENUMS[sKey]];
    input.innerHTML = options.map(o => `<option ${o === value ? 'selected' : ''}>${esc(o)}</option>`).join('');
    input.addEventListener('change', () => setValue(path, input.value));
  } else if (typeof value === 'boolean') {
    input = document.createElement('select');
    input.innerHTML = `<option value="true" ${value ? 'selected' : ''}>ja</option><option value="false" ${value ? '' : 'selected'}>nein</option>`;
    input.addEventListener('change', () => setValue(path, input.value === 'true'));
  } else if (typeof value === 'number') {
    input = document.createElement('input');
    input.type = 'number';
    input.value = value;
    input.addEventListener('input', () => setValue(path, input.value === '' ? null : Number(input.value)));
  } else if (Array.isArray(value)) {
    input = document.createElement('input');
    input.value = value.join(', ');
    input.placeholder = 'kommagetrennt, z. B. DE, US';
    input.addEventListener('input', () => setValue(path, input.value.split(',').map(s => s.trim()).filter(Boolean)));
  } else if (/freitext|textauszug|erlaeuterung|kontozweck/.test(String(key))) {
    input = document.createElement('textarea');
    input.rows = 2;
    input.value = value ?? '';
    input.addEventListener('input', () => setValue(path, input.value));
    wrapper.classList.add('wide');
  } else {
    input = document.createElement('input');
    input.value = value ?? '';
    input.addEventListener('input', () => setValue(path, input.value));
  }
  wrapper.appendChild(input);
  return wrapper;
}

function renderEmployer(container, value, path) {
  const group = document.createElement('div');
  group.className = 'subgroup';
  const head = document.createElement('div');
  head.className = 'subgroup-head';
  head.innerHTML = `<span>Arbeitgeber</span>`;
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'ghost small';
  toggle.textContent = value ? 'entfernen (kein Arbeitgeber)' : 'Arbeitgeber erfassen';
  toggle.addEventListener('click', () => {
    setValue(path, value ? null : EMPLOYER_TEMPLATE());
    renderForm();
  });
  head.appendChild(toggle);
  group.appendChild(head);
  if (value) {
    const grid = document.createElement('div');
    grid.className = 'grid';
    for (const [childKey, childValue] of Object.entries(value)) grid.appendChild(renderInput(childValue, [...path, childKey]));
    group.appendChild(grid);
  } else {
    group.insertAdjacentHTML('beforeend', '<p class="hint">Kein Arbeitgeber (null), z. B. bei Selbstständigkeit oder Ruhestand.</p>');
  }
  container.appendChild(group);
}

function renderObjectList(container, list, path) {
  const sKey = schemaKey(path);
  const group = document.createElement('div');
  group.className = 'subgroup';
  const head = document.createElement('div');
  head.className = 'subgroup-head';
  head.innerHTML = `<span>${esc(label(path[path.length - 1]))} (${list.length})</span>`;
  if (ITEM_TEMPLATES[sKey]) {
    const add = document.createElement('button');
    add.type = 'button';
    add.className = 'ghost small';
    add.textContent = '+ hinzufügen';
    add.addEventListener('click', () => {
      list.push(ITEM_TEMPLATES[sKey](list));
      syncJson();
      renderForm();
    });
    head.appendChild(add);
  }
  group.appendChild(head);
  list.forEach((item, index) => {
    const grid = document.createElement('div');
    grid.className = 'grid';
    for (const [childKey, childValue] of Object.entries(item)) grid.appendChild(renderInput(childValue, [...path, index, childKey]));
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'ghost small';
    remove.textContent = 'entfernen';
    remove.addEventListener('click', () => {
      list.splice(index, 1);
      syncJson();
      renderForm();
    });
    const field = document.createElement('div');
    field.className = 'field';
    field.appendChild(remove);
    grid.appendChild(field);
    group.appendChild(grid);
  });
  if (!list.length) group.insertAdjacentHTML('beforeend', '<p class="hint">keine</p>');
  container.appendChild(group);
}

function syncJson() {
  $('#json-text').value = JSON.stringify(state.application, null, 2);
}

function setupJsonEditor() {
  $('#toggle-json').addEventListener('click', () => {
    const editor = $('#json-editor');
    editor.hidden = !editor.hidden;
    $('#application-form').hidden = !editor.hidden;
    $('#toggle-json').textContent = editor.hidden ? 'JSON' : 'Formular';
  });
  $('#json-apply').addEventListener('click', () => {
    try {
      state.application = JSON.parse($('#json-text').value);
      $('#json-error').textContent = '';
      renderForm();
    } catch (e) {
      $('#json-error').textContent = `Ungültiges JSON: ${e.message}`;
    }
  });
}

async function startCheck() {
  const button = $('#start-button');
  button.disabled = true;
  button.textContent = 'Prüfung läuft …';
  const panel = $('#check-result');
  try {
    if (!$('#json-editor').hidden) state.application = JSON.parse($('#json-text').value);
    normalizeEmployer(state.application);
    const result = await api('/kyc_review', { method: 'POST', body: JSON.stringify({ application: state.application }) });
    renderCheckResult(result);
    refreshReviewCount();
  } catch (e) {
    panel.innerHTML = `<h2>Ergebnis</h2><p class="error">${esc(e.message)}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = 'Prüfung starten';
  }
}

/* Ein angelegtes, aber leer gelassenes Arbeitgeberformular bedeutet „kein Arbeitgeber“ (null), wie im Schema. */
function normalizeEmployer(application) {
  const employment = application?.beschaeftigung;
  const employer = employment?.arbeitgeber;
  if (employer && Object.values(employer).every(v => String(v ?? '').trim() === '')) {
    employment.arbeitgeber = null;
    renderForm();
    syncJson();
  }
}

function renderCheckResult(result) {
  const llm = result.llm_result;
  const autoApproved = result.rule_result === 'green' && llm && llm.decision === 'keine_manuelle_pruefung';
  const ruleRejected = result.rule_result === 'reject';
  const outcome = ruleRejected
    ? `<div class="outcome bad">Abgelehnt durch Regeln<small>Ausschlussgrund liegt vor; keine LLM-Prüfung und keine manuelle Prüfung.</small></div>`
    : autoApproved
    ? `<div class="outcome ok">Automatisch freigegeben<small>Regeln grün und Laya: keine manuelle Prüfung.</small></div>`
    : `<div class="outcome warn">Manuelle Prüfung erforderlich<small>${result.rule_result !== 'green' ? 'Regeltrigger erzwingt die Prüfung.' : 'Laya empfiehlt eine Prüfung oder konnte nicht bewerten.'}</small></div>`;
  $('#check-result').innerHTML = `
    <div class="panel-head"><h2>Ergebnis</h2><code title="Prozessinstanz">${esc(result.id.slice(0, 8))}</code></div>
    <div class="flow">
      <div class="stage">
        <div class="stage-head"><strong>1 · Prüfung nach Regeln</strong>${ruleBadge(result.rule_result, result.triggered_rules)}</div>
        ${rulesTable(result.application, result.triggered_rules)}
      </div>
      <div class="stage">
        <div class="stage-head"><strong>2 · Prüfung mit LLM (Laya)</strong>${decisionBadge(llm && llm.decision)}</div>
        ${ruleRejected ? '<p class="note">Nicht ausgeführt: Ablehnung durch Regeln.</p>' : llmBars(llm)}
      </div>
      ${outcome}
      <div class="row gap end">
        ${autoApproved || ruleRejected ? '' : '<a href="#review"><button type="button">Zur manuellen Prüfung</button></a>'}
        <a href="#dashboard/${esc(result.id)}"><button type="button" class="primary">Im Dashboard ansehen</button></a>
      </div>
    </div>`;
}

/* ---------- Ansicht: Manuelle Prüfung ---------- */

function reviewerQuery() {
  const user = encodeURIComponent($('#reviewer').value.trim() || 'anna');
  return `user=${user}&group=${REVIEW_GROUP}`;
}

async function loadTasks() {
  const tasks = await api(`/usertasks/instance?${reviewerQuery()}`);
  return tasks.filter(t => ['Ready', 'Reserved'].includes(t.status.name));
}

async function refreshReviewCount() {
  try {
    const tasks = await loadTasks();
    const badge = $('#review-count');
    badge.textContent = tasks.length;
    badge.hidden = tasks.length === 0;
    return tasks;
  } catch {
    return [];
  }
}

async function renderReview() {
  const tasks = await refreshReviewCount();
  const list = $('#task-list');
  if (!tasks.length) {
    list.innerHTML = '<li class="empty"><p>Keine offenen Prüfungen.</p></li>';
    if (state.selectedTaskId) {
      state.selectedTaskId = null;
      $('#task-detail').innerHTML = '<div class="empty"><h2>Prüfung</h2><p>Keine offene Prüfung ausgewählt.</p></div>';
    }
    return;
  }
  list.innerHTML = tasks.map(t => {
    const app = t.inputs.application || {};
    const name = `${app.kunde?.vorname || ''} ${app.kunde?.nachname || ''}`.trim();
    const rules = t.inputs.triggered_rules || [];
    return `<li data-id="${esc(t.id)}" class="${t.id === state.selectedTaskId ? 'selected' : ''}">
      <div class="item-top"><span class="item-name">${esc(name || 'Unbekannt')}</span>
        <span class="badge ${t.status.name === 'Reserved' ? 'info' : ''}">${t.status.name === 'Reserved' ? `übernommen: ${esc(t.actualOwner)}` : 'offen'}</span></div>
      <div class="item-meta">${ruleBadge(rules.length ? 'review' : 'green', rules)} ${decisionBadge(t.inputs.llm_result?.decision)}</div>
    </li>`;
  }).join('');
  list.querySelectorAll('li[data-id]').forEach(li => li.addEventListener('click', () => {
    state.selectedTaskId = li.dataset.id;
    renderReview();
  }));
  const selected = tasks.find(t => t.id === state.selectedTaskId);
  if (selected) renderTaskDetail(selected);
}

function renderTaskDetail(task) {
  const detail = $('#task-detail');
  if (detail.dataset.taskId === task.id && detail.dataset.status === task.status.name) return;
  detail.dataset.taskId = task.id;
  detail.dataset.status = task.status.name;
  const app = task.inputs.application || {};
  detail.innerHTML = `
    <div class="panel-head"><h2>Manuelle Prüfung</h2>
      <a href="#dashboard/${esc(task.processInfo.processInstanceId)}">Ablauf im Dashboard</a></div>
    ${applicationSummary(app)}
    <div class="detail-grid">
      <div class="stage"><h3>Regeln (DMN)</h3>${rulesTable(app, task.inputs.triggered_rules)}</div>
      <div class="stage"><h3>Laya</h3>${llmBars(task.inputs.llm_result)}</div>
    </div>
    <div class="decision-box">
      <label class="field wide"><span>Kommentar</span><textarea id="review-comment" rows="3" placeholder="Ergebnis der Klärung"></textarea></label>
      <div class="row gap end">
        <span class="error" id="review-error"></span>
        <button type="button" class="reject" data-decision="reject">Ablehnen</button>
        <button type="button" class="approve" data-decision="approve">Freigeben</button>
      </div>
    </div>`;
  detail.querySelectorAll('button[data-decision]').forEach(button =>
    button.addEventListener('click', () => completeTask(task, button.dataset.decision)));
}

async function completeTask(task, decision) {
  const url = `/usertasks/instance/${task.id}/transition?${reviewerQuery()}`;
  const comment = $('#review-comment').value.trim();
  $('#task-detail').querySelectorAll('button').forEach(b => { b.disabled = true; });
  try {
    if (task.status.name === 'Ready') await api(url, { method: 'POST', body: JSON.stringify({ transitionId: 'claim' }) });
    await api(url, { method: 'POST', body: JSON.stringify({ transitionId: 'complete', data: { decision, comment } }) });
    state.selectedTaskId = null;
    const detail = $('#task-detail');
    delete detail.dataset.taskId;
    detail.innerHTML = `<div class="empty"><h2>Prüfung abgeschlossen</h2>
      <p>${decision === 'approve' ? 'Freigegeben' : 'Abgelehnt'}. <a href="#dashboard/${esc(task.processInfo.processInstanceId)}">Ablauf im Dashboard ansehen</a></p></div>`;
    renderReview();
  } catch (e) {
    $('#review-error').textContent = e.message;
    $('#task-detail').querySelectorAll('button').forEach(b => { b.disabled = false; });
  }
}

/* ---------- Ansicht: Dashboard ---------- */

function setupViewer() {
  // Externe Beschriftungen bricht bpmn-js fest bei 90 px um; kleinere Schrift vermeidet Worttrennungen.
  state.viewer = new BpmnJS({ container: '#canvas', textRenderer: { externalStyle: { fontSize: 10, lineHeight: 1.2 } } });
  // Nur importieren: Beim Start ist das Dashboard oft ausgeblendet, ein Zoom auf einen
  // Container der Größe 0 schlägt fehl. Gezoomt wird erst, wenn das Diagramm sichtbar ist.
  state.diagramReady = api('/api/dashboard/process.bpmn').then(xml => state.viewer.importXML(xml));
  state.diagramReady.catch(e => console.error('BPMN-Import fehlgeschlagen', e));
}

/* Passt das Diagramm in den sichtbaren Bereich ein. bpmn-js merkt sich die Containergröße; wurde
 * es versteckt (0×0) initialisiert, ergibt jeder Zoom eine NaN-Matrix und das Diagramm bleibt
 * unsichtbar. Deshalb: Größe neu einlesen und den Ausschnitt aus den Diagrammgrenzen setzen. */
function fitDiagram() {
  const container = $('#canvas');
  if (!state.viewer || container.offsetWidth === 0) return Promise.resolve();
  return state.diagramReady.then(() => {
    const canvas = state.viewer.get('canvas');
    canvas.resized();
    const bounds = diagramBounds();
    if (!bounds) return;
    const margin = 30;
    canvas.viewbox({
      x: bounds.minX - margin,
      y: bounds.minY - margin,
      width: bounds.maxX - bounds.minX + 2 * margin,
      height: bounds.maxY - bounds.minY + 2 * margin,
    });
  }).catch(e => console.warn('Diagramm konnte nicht eingepasst werden', e));
}

function diagramBounds() {
  const points = [];
  state.viewer.get('elementRegistry').getAll().forEach(element => {
    if (element.waypoints) {
      element.waypoints.forEach(p => points.push([p.x, p.y]));
    } else if (element.width && element.type !== 'bpmn:Process') {
      points.push([element.x, element.y], [element.x + element.width, element.y + element.height]);
    }
  });
  if (!points.length) return null;
  return {
    minX: Math.min(...points.map(p => p[0])), minY: Math.min(...points.map(p => p[1])),
    maxX: Math.max(...points.map(p => p[0])), maxY: Math.max(...points.map(p => p[1])),
  };
}

function diagramNeedsFit() {
  const transform = document.querySelector('#canvas .viewport')?.getAttribute('transform') || '';
  return transform === '' || transform.includes('NaN');
}

async function renderDashboard() {
  const instances = await api('/api/dashboard/instances');
  renderKpis(instances);
  const filter = $('#instance-filter').value;
  const visible = instances.filter(i => filter === 'all' || (filter === 'active' ? i.status === 'active' : i.status !== 'active'));
  const list = $('#instance-list');
  list.innerHTML = visible.length ? visible.map(i => {
    const outcome = outcomeOf(i);
    return `<li data-id="${esc(i.id)}" class="${i.id === state.selectedInstanceId ? 'selected' : ''}">
      <div class="item-top"><span class="item-name">${esc(i.customer || 'Unbekannt')}</span><span class="badge ${outcome.tone}">${esc(outcome.text)}</span></div>
      <div class="item-meta"><span>${formatTime(i.start)}</span>${ruleBadge(i.ruleResult, i.triggeredRules)}${decisionBadge(i.llmDecision)}</div>
    </li>`;
  }).join('') : '<li class="empty"><p>Noch keine Instanzen. Unter „Antrag prüfen“ einen Fall starten.</p></li>';
  list.querySelectorAll('li[data-id]').forEach(li => li.addEventListener('click', () => {
    location.hash = `#dashboard/${li.dataset.id}`;
  }));
  if (!state.selectedInstanceId && visible.length) state.selectedInstanceId = visible[0].id;
  if (state.selectedInstanceId) await renderInstance(state.selectedInstanceId);
}

function renderKpis(instances) {
  const count = predicate => instances.filter(predicate).length;
  const kpis = [
    ['Instanzen', instances.length],
    ['automatisch freigegeben', count(i => i.outcome === 'approved' && !i.manualDecision)],
    ['in manueller Prüfung', count(i => i.status === 'active')],
    ['nach Prüfung freigegeben', count(i => i.outcome === 'approved' && i.manualDecision)],
    ['abgelehnt', count(i => i.outcome === 'rejected')],
    ['Laya-Fehler', count(i => i.llmDecision === 'fehler')],
  ];
  $('#kpis').innerHTML = kpis.map(([text, value]) =>
    `<div class="kpi"><div class="kpi-value">${value}</div><div class="kpi-label">${esc(text)}</div></div>`).join('');
}

async function renderInstance(id) {
  let instance;
  try {
    instance = await api(`/api/dashboard/instances/${encodeURIComponent(id)}`);
  } catch {
    state.selectedInstanceId = null;
    return;
  }
  const key = JSON.stringify([instance.id, instance.status, instance.steps.length, instance.manualDecision]);
  if (key === state.lastDetailKey) return;
  state.lastDetailKey = key;
  const outcome = outcomeOf({ ...instance, waitingAt: instance.status === 'active' ? instance.steps.at(-1)?.name : null });
  $('#instance-title').innerHTML = `${esc(instance.customer || 'Instanz')} <span class="badge ${outcome.tone}">${esc(outcome.text)}</span>`;
  renderInstanceCards(instance);
  try {
    await highlightDiagram(instance);
  } catch (e) {
    // Beim nächsten Aktualisieren erneut versuchen, statt den Stand als dargestellt zu merken.
    state.lastDetailKey = null;
    console.error('Pfad konnte nicht markiert werden', e);
  }
}

async function highlightDiagram(instance) {
  await state.diagramReady;
  if (diagramNeedsFit()) await fitDiagram();
  const canvas = state.viewer.get('canvas');
  const registry = state.viewer.get('elementRegistry');
  const overlays = state.viewer.get('overlays');
  state.markers.forEach(([elementId, cls]) => canvas.removeMarker(elementId, cls));
  state.markers = [];
  overlays.clear();
  const mark = (elementId, cls) => {
    canvas.addMarker(elementId, cls);
    state.markers.push([elementId, cls]);
  };

  const visited = new Set(instance.steps.map(s => s.nodeId));
  const transitions = new Set();
  instance.steps.forEach((s, i) => { if (i > 0) transitions.add(`${instance.steps[i - 1].nodeId}>${s.nodeId}`); });
  const waiting = instance.status === 'active' ? instance.steps.at(-1)?.nodeId : null;

  registry.getAll().forEach(element => {
    if (element.type === 'bpmn:Process' || element.type === 'label' || !element.businessObject) return;
    if (element.waypoints) {
      const bo = element.businessObject;
      const taken = bo.sourceRef && bo.targetRef && transitions.has(`${bo.sourceRef.id}>${bo.targetRef.id}`);
      mark(element.id, taken ? 'visited' : 'dimmed');
    } else if (element.id === waiting) {
      mark(element.id, 'current');
    } else if (visited.has(element.id)) {
      mark(element.id, instance.status === 'error' && element.id === instance.steps.at(-1)?.nodeId ? 'failed' : 'visited');
    } else {
      mark(element.id, 'dimmed');
    }
  });

  const badge = (elementId, text, tone) => {
    if (!registry.get(elementId)) return;
    overlays.add(elementId, { position: { bottom: 10, left: 0 }, html: `<div class="diagram-badge ${tone}">${esc(text)}</div>` });
  };
  if (instance.ruleResult) {
    badge('Task_Rules', instance.ruleResult === 'green' ? 'DMN: grün' : `DMN: ${(instance.triggeredRules || []).join(', ')}`,
      instance.ruleResult === 'green' ? 'ok' : instance.ruleResult === 'reject' ? 'bad' : 'warn');
  }
  if (instance.llmResult) {
    const d = instance.llmResult;
    const p = d.probabilities?.[d.decision];
    badge('Task_LLM', `${DECISIONS[d.decision]?.label || d.decision}${p != null ? ` · ${(p * 100).toFixed(0)} %` : ''}`, DECISIONS[d.decision]?.tone || '');
  }
  if (instance.manualDecision) {
    badge('Task_Manual', instance.manualDecision === 'approve' ? 'Freigegeben' : instance.manualDecision === 'reject' ? 'Abgelehnt' : `ungültig: ${instance.manualDecision}`,
      instance.manualDecision === 'approve' ? 'ok' : 'bad');
  }
}

function renderInstanceCards(instance) {
  const manual = instance.manualDecision
    ? `<table class="kv"><tr><td>Entscheidung</td><td>${instance.manualDecision === 'approve' ? '<span class="badge ok">Freigabe</span>' : instance.manualDecision === 'reject' ? '<span class="badge bad">Ablehnung</span>' : esc(instance.manualDecision)}</td></tr>
       <tr><td>Kommentar</td><td>${esc(instance.manualComment || '–')}</td></tr></table>`
    : instance.status === 'active'
      ? `<p class="note">Wartet auf manuelle Prüfung. <a href="#review">Zur Prüfung</a></p>`
      : '<p class="note">Keine manuelle Prüfung erforderlich.</p>';
  const steps = instance.steps.map((s, i) => {
    const isWaiting = instance.status === 'active' && i === instance.steps.length - 1;
    return `<li class="${isWaiting ? 'waiting' : ''}"><span class="time">${formatTime(s.entered).slice(0, 12)}</span>
      <span class="name">${esc(NODE_LABELS[s.nodeId] || s.name || s.nodeId)}</span>
      <span class="dur">${isWaiting ? 'wartet' : formatDuration(s.entered, s.left)}</span></li>`;
  }).join('');
  $('#instance-cards').innerHTML = `
    <div class="panel span-2"><h3>DMN-Ergebnis · Prüfung nach Regeln</h3>
      <div class="stage-head">${ruleBadge(instance.ruleResult, instance.triggeredRules)}</div>
      ${rulesTable(instance.application, instance.triggeredRules)}</div>
    <div class="panel"><h3>LLM-Ergebnis · Laya</h3>
      <div class="stage-head">${decisionBadge(instance.llmResult?.decision)}</div>
      ${llmBars(instance.llmResult)}</div>
    <div class="panel"><h3>Manuelle Prüfung</h3>${manual}</div>
    <div class="panel"><h3>Verlauf</h3>
      <p class="note">Start ${formatTime(instance.start)}${instance.end ? ` · Ende ${formatTime(instance.end)} · Dauer ${formatDuration(instance.start, instance.end)}` : ''}</p>
      <ul class="timeline">${steps}</ul></div>
    <div class="panel"><h3>Antrag</h3>${applicationSummary(instance.application)}</div>`;
}

/* ---------- Status, Navigation, Aktualisierung ---------- */

async function refreshServiceStatus() {
  const set = (id, up, title) => {
    const el = $(id);
    el.classList.toggle('up', up);
    el.classList.toggle('down', !up);
    el.title = title;
  };
  try {
    const status = await api('/api/dashboard/status');
    set('#status-kogito', true, 'Kogito erreichbar');
    const laya = status.laya || {};
    set('#status-laya', laya.status === 'ok', laya.status === 'ok' ? `Laya: ${laya.device}` : `Laya: ${laya.error || laya.status}`);
  } catch (e) {
    set('#status-kogito', false, e.message);
    set('#status-laya', false, 'unbekannt');
  }
}

function currentView() {
  const [view, id] = location.hash.replace('#', '').split('/');
  return { view: ['check', 'review', 'dashboard'].includes(view) ? view : 'check', id };
}

function showView() {
  const { view, id } = currentView();
  document.querySelectorAll('.view').forEach(section => { section.hidden = section.id !== `view-${view}`; });
  document.querySelectorAll('.tabs a').forEach(a => a.classList.toggle('active', a.dataset.view === view));
  if (view === 'dashboard') {
    if (id && id !== state.selectedInstanceId) {
      state.selectedInstanceId = id;
      state.lastDetailKey = null;
    }
    fitDiagram();
    renderDashboard().catch(e => console.error(e));
  }
  if (view === 'review') renderReview();
}

function tick() {
  const { view } = currentView();
  const work = view === 'dashboard' ? renderDashboard() : view === 'review' ? renderReview() : refreshReviewCount();
  Promise.resolve(work).catch(() => {}).finally(() => setTimeout(tick, REFRESH_MS));
}

async function init() {
  setupViewer();
  setupJsonEditor();
  $('#start-button').addEventListener('click', startCheck);
  $('#instance-filter').addEventListener('change', () => renderDashboard());
  $('#reviewer').addEventListener('change', () => { state.selectedTaskId = null; renderReview(); });
  $('#clear-history').addEventListener('click', async () => {
    await api('/api/dashboard/instances', { method: 'DELETE' });
    state.selectedInstanceId = null;
    state.lastDetailKey = null;
    $('#instance-cards').innerHTML = '';
    $('#instance-title').textContent = 'Prozessablauf';
    renderDashboard();
  });
  window.addEventListener('hashchange', showView);
  window.addEventListener('resize', () => { if (currentView().view === 'dashboard') fitDiagram(); });
  await loadCases();
  showView();
  refreshServiceStatus();
  setInterval(refreshServiceStatus, 10000);
  setTimeout(tick, REFRESH_MS);
}

init();
