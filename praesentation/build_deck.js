// Erzeugt die Präsentation "Vertical AI im KYC-Prozess" im Stil von piu.de.
// Stil: weiß, Fast-Schwarz, Menlo (Monospace) durchgehend, BPMN-Formen als Motiv wie im Logo.
// Auf den Folien nur Oberpunkte; Erläuterungen stehen in den Sprechernotizen.
//
//   NODE_PATH=<node_modules mit pptxgenjs> node build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME_JS);

const OUT = path.join(__dirname, "Vertical_AI_KYC.pptx");
const LOGO = path.join(__dirname, "assets", "logo_piu.png");          // 4968 x 736 px
const PROCESS = path.join(__dirname, "assets", "kyc_prozess.png");    // 3963 x 1236 px
const LOGO_KOGITO = path.join(__dirname, "assets", "logo_kogito.png"); // 1279 x 359 px, Apache KIE
const LOGO_CIB = path.join(__dirname, "assets", "logo_cib.png");       // 2400 x 1087 px, CIB software GmbH
const LOGO_RATIO = 736 / 4968;
const PROCESS_RATIO = 1236 / 3963;

const INK = "121212";
const GREY = "757575";
const LIGHT = "F4F4F4";

const THEME = {
  name: "piu Prozesse im Unternehmen",
  headFontFace: "Menlo",
  bodyFontFace: "Menlo",
  colors: {
    dk1: INK, lt1: "FFFFFF", dk2: "2B2B2B", lt2: LIGHT,
    accent1: INK, accent2: GREY, accent3: "EFEFEF", accent4: "2B2B2B", accent5: "9B0103", accent6: "ABB8C3",
    hlink: INK, folHlink: GREY,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Vertical AI im KYC-Prozess";
pres.company = "piu – Prozesse im Unternehmen";
const C = pres.SchemeColor;

const W = 13.333;
const MARGIN = 0.6;

// ---------- Layouts ----------
pres.defineSlideMaster({
  title: "TITLE",
  background: { color: "FFFFFF" },
  objects: [
    { image: { path: LOGO, x: MARGIN, y: 0.6, w: 4.2, h: 4.2 * LOGO_RATIO } },
    { placeholder: { options: { name: "title", type: "title", x: MARGIN, y: 2.55, w: W - 2 * MARGIN, h: 1.3,
      fontSize: 54, bold: true, color: C.text1, align: "left", valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: MARGIN, y: 4.0, w: W - 2 * MARGIN, h: 1.0,
      fontSize: 22, color: C.text1, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  objects: [
    { image: { path: LOGO, x: MARGIN, y: 6.95, w: 1.9, h: 1.9 * LOGO_RATIO } },
    { placeholder: { options: { name: "title", type: "title", x: MARGIN, y: 0.45, w: W - 2 * MARGIN, h: 0.9,
      fontSize: 30, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - MARGIN - 0.6, y: 6.9, w: 0.6, h: 0.35, fontSize: 11, color: GREY, align: "right" },
});

// ---------- BPMN-Motiv ----------
function task(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.12, x, y, w, h,
    fill: { color: opts.fill || "FFFFFF" }, line: { color: INK, width: opts.lineWidth || 1.5 },
    fontSize: opts.fontSize || 16, bold: !!opts.bold, color: C.text1, align: opts.align || "center", valign: "middle",
    margin: 10, objectName: opts.name || `Aufgabe ${text.slice(0, 24)}`,
  });
}
function startEvent(slide, x, y, d = 0.42) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: "FFFFFF" }, line: { color: INK, width: 1.5 }, objectName: "Startereignis" });
}
function endEvent(slide, x, y, d = 0.42) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: "FFFFFF" }, line: { color: INK, width: 4 }, objectName: "Endereignis" });
}
function gateway(slide, x, y, d = 0.75) {
  slide.addText("X", { shape: pres.shapes.DIAMOND, x, y, w: d, h: d, fill: { color: "FFFFFF" }, line: { color: INK, width: 1.5 },
    fontSize: 16, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, objectName: "Gateway" });
}
function arrow(slide, x1, y1, x2, y2) {
  slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1, line: { color: INK, width: 1.5, endArrowType: "triangle" }, objectName: "Sequenzfluss" });
}
// Dicker schwarzer Balken links, wie die Zitate auf piu.de
function quoteBar(slide, x, y, h) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.075, h, fill: { color: INK }, line: { color: INK, width: 0 }, objectName: "Zitatbalken" });
}

// ---------- Folien ----------

// 1 Titel
pres.addSection({ title: "Einstieg" });
let s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Einstieg" });
s.addText("Vertical AI", { placeholder: "title" });
s.addText("KYC-Prüfung mit Regeln, KI und manueller Prüfung", { placeholder: "body" });
// kleine Prozesskette als Bildmotiv
startEvent(s, MARGIN, 5.9);
arrow(s, MARGIN + 0.42, 6.11, MARGIN + 1.1, 6.11);
task(s, "Regeln", MARGIN + 1.1, 5.75, 1.9, 0.72, { fontSize: 14 });
arrow(s, MARGIN + 3.0, 6.11, MARGIN + 3.6, 6.11);
task(s, "KI", MARGIN + 3.6, 5.75, 1.9, 0.72, { fontSize: 14 });
arrow(s, MARGIN + 5.5, 6.11, MARGIN + 6.1, 6.11);
task(s, "Mensch", MARGIN + 6.1, 5.75, 1.9, 0.72, { fontSize: 14 });
arrow(s, MARGIN + 8.0, 6.11, MARGIN + 8.6, 6.11);
endEvent(s, MARGIN + 8.6, 5.9);
s.addNotes("Vertical AI am Beispiel KYC: Regeln, ein lokal trainiertes Entscheidungsmodell und die manuelle Prüfung im BPMN-Prozess.");

// 2 TL;DR
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Einstieg" });
s.addText("TL;DR – Too long, didn't read", { placeholder: "title" });
const statements = [
  "Regeln sind immer effizienter als Intelligenz – ob künstlich oder natürlich",
  "Vertical AI schützt interne Daten",
  "Das Modell lernt, was in den Daten steckt – nicht, was wir gern hätten!",
  "Der Prozess entscheidet, wann der Mensch prüft – nicht die KI",
  "Spezialisierte KI ist klein, lokal trainierbar, schnell und günstig",
];
const rowY = 1.75, rowH = 0.92;
quoteBar(s, MARGIN, rowY, rowH * statements.length - 0.2);
statements.forEach((text, i) => {
  s.addText([
    { text: `${i + 1}. `, options: { bold: true } },
    { text },
  ], { x: MARGIN + 0.35, y: rowY + i * rowH, w: W - 2 * MARGIN - 0.35, h: rowH - 0.2, fontSize: 19, color: C.text1,
       valign: "middle", margin: 0, isTextBox: true, objectName: `Kernaussage ${i + 1}` });
});
s.addNotes(
  "Anekdote: TL;DR kennt man von langen Texten – hier die Kurzfassung des Vortrags vorweg.\n" +
  "1. Regeln: DMN-Regeln entscheiden in 1 ms, Laya in 80–250 ms, ein Mensch in Minuten. R4 (USA-Bezug) war in Minuten umgesetzt, eine Korrektur am Modell kostete ein Neutraining.\n" +
  "2. Vertical AI schützt interne Daten: Modell läuft und lernt im eigenen Haus auf einem Mac; keine Kundendaten verlassen die Bank.\n" +
  "3. Das Modell reagierte auf den Dokumenttyp 'Rücklagenbestätigung' statt auf die Wohnadresse an der Reeperbahn.\n" +
  "4. Regeltrigger kann das Modell nicht aufheben; bei technischem Fehler geht der Fall in die manuelle Prüfung.\n" +
  "5. 322 Mio. Parameter, Training in rund 1,5 Stunden auf einem Mac.");

// 3 Use Case
pres.addSection({ title: "Use Case und Prozess" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Use Case und Prozess" });
s.addText("Use Case: KYC bei der Kontoeröffnung", { placeholder: "title" });
s.addText("Privatkunden · nach erfolgreicher Identitätsprüfung · vor der Kontoanlage", {
  x: MARGIN, y: 1.35, w: W - 2 * MARGIN, h: 0.45, fontSize: 16, color: GREY, margin: 0, isTextBox: true, objectName: "Untertitel" });
quoteBar(s, MARGIN, 2.15, 1.05);
s.addText("Muss dieser Antrag manuell geprüft werden?", {
  x: MARGIN + 0.35, y: 2.15, w: W - 2 * MARGIN - 0.35, h: 1.05, fontSize: 28, bold: true, color: C.text1, valign: "middle",
  margin: 0, isTextBox: true, objectName: "Leitfrage" });
// BPMN-Skizze: Antrag → Gateway → Freigabe / Ablehnung / manuelle Prüfung
const fy = 4.6;
startEvent(s, MARGIN, fy + 0.15);
arrow(s, MARGIN + 0.42, fy + 0.36, MARGIN + 1.0, fy + 0.36);
task(s, "Kontoantrag", MARGIN + 1.0, fy, 2.4, 0.72);
arrow(s, MARGIN + 3.4, fy + 0.36, MARGIN + 4.0, fy + 0.36);
gateway(s, MARGIN + 4.0, fy - 0.015);
arrow(s, MARGIN + 4.375, fy - 0.015, MARGIN + 4.375, fy - 0.79);
arrow(s, MARGIN + 4.375, fy - 0.79, MARGIN + 5.5, fy - 0.79);
task(s, "Automatische Freigabe", MARGIN + 5.5, fy - 1.15, 3.4, 0.72);
arrow(s, MARGIN + 4.75, fy + 0.36, MARGIN + 5.5, fy + 0.36);
task(s, "Ablehnung", MARGIN + 5.5, fy, 3.4, 0.72);
arrow(s, MARGIN + 4.375, fy + 0.735, MARGIN + 4.375, fy + 1.51);
arrow(s, MARGIN + 4.375, fy + 1.51, MARGIN + 5.5, fy + 1.51);
task(s, "Manuelle Prüfung", MARGIN + 5.5, fy + 1.15, 3.4, 0.72);
s.addNotes("Die Frage: Muss dieser Antrag vor der Kontoanlage manuell geprüft werden oder kann er automatisch freigegeben werden? " +
  "Ausgangslage: Identität ist geprüft; bewertet werden Selbstauskunft, Screening und eingereichte Unterlagen. " +
  "Drei Ausgänge: automatische Freigabe, Ablehnung bei eindeutigem Ausschlussgrund (z. B. bestätigter Sanktionstreffer) oder manuelle Prüfung. " +
  "Dilemma: alles manuell prüfen ist teuer, alles automatisch freigeben ist riskant. Fiktive Demo-Richtlinie, synthetische Daten.");

// 4 Prozess
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Use Case und Prozess" });
s.addText("Der Prozess (BPMN)", { placeholder: "title" });
const pw = W - 2 * MARGIN, ph = pw * PROCESS_RATIO;
s.addImage({ path: PROCESS, x: MARGIN, y: 1.55 + (5.1 - ph) / 2, w: pw, h: ph, altText: "BPMN-Prozess: Prüfung nach Regeln, Prüfung mit LLM, manuelle Prüfung, Freigabe oder Ablehnung", objectName: "BPMN-Diagramm" });
s.addNotes("Ablauf: Regeln (DMN) → Prüfung mit LLM (Laya) → Gateway → manuelle Prüfung → Freigabe oder Ablehnung. " +
  "Automatische Freigabe nur bei grünen Regeln UND LLM-Entscheidung 'keine manuelle Prüfung'. " +
  "Ein bestätigter Sanktionstreffer (R5) lehnt direkt am ersten Gateway ab, ohne LLM. " +
  "Fällt Laya aus, geht der Fall in die manuelle Prüfung. Ausgeführt mit Kogito 10.2.");

// 5 Regeln
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Use Case und Prozess" });
s.addText("Die Regeln (DMN)", { placeholder: "title" });
const head = (t) => ({ text: t, options: { bold: true, color: C.text1, fill: { color: LIGHT } } });
const rules = [
  ["R1", "Kunde nicht selbst wirtschaftlich berechtigt"],
  ["R2", "PEP-Status bestätigt"],
  ["R3", "Möglicher Screening-Treffer ungeklärt"],
  ["R4", "USA-Bezug"],
  ["R5", "Bestätigter Sanktionstreffer", "Ablehnung"],
];
s.addTable([
  [head("Regel"), head("Bedingung"), head("Folge")],
  ...rules.map(([id, cond, effect = "manuelle Prüfung"]) => [
    { text: id, options: { bold: true } }, { text: cond }, { text: effect, options: { bold: effect !== "manuelle Prüfung" } },
  ]),
], { x: MARGIN, y: 1.75, w: W - 2 * MARGIN, colW: [1.4, 7.4, W - 2 * MARGIN - 8.8], rowH: 0.72, fontSize: 18, color: C.text1,
     valign: "middle", border: { type: "solid", pt: 1, color: "C8C8C8" }, margin: [0, 0.15, 0, 0.15], objectName: "Regeltabelle" });
s.addNotes("Entscheidungstabelle KYC_RuleCheck mit Trefferpolitik COLLECT; R1–R4 erzwingen die manuelle Prüfung. R5 (bestätigter Sanktionstreffer) ist der einzige Ausschlussgrund: Ablehnung ohne LLM und ohne manuelle Prüfung. " +
  "R4 (USA-Bezug: US-Steuerpflicht, FATCA, Staatsangehörigkeit, Ansässigkeit oder Adresse USA) war in Minuten ergänzt – ohne Training. Zurück zu Kernaussage 1.");

// 6 Datensatz
pres.addSection({ title: "Daten und Modell" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Daten und Modell" });
s.addText("Am Anfang steht ein Datensatz", { placeholder: "title" });
const stats = [["6.000", "synthetische Anträge"], ["4.781", "Training"], ["598", "Validierung"], ["621", "Test"]];
const sw = (W - 2 * MARGIN - 3 * 0.4) / 4;
stats.forEach(([num, label], i) => {
  const x = MARGIN + i * (sw + 0.4);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.1, w: sw, h: 2.6, rectRadius: 0.12, fill: { color: i === 0 ? LIGHT : "FFFFFF" },
    line: { color: INK, width: 1.5 }, objectName: `Kennzahl ${label}` });
  s.addText(num, { x, y: 2.45, w: sw, h: 1.1, fontSize: 44, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Zahl ${label}` });
  s.addText(label, { x, y: 3.65, w: sw, h: 0.7, fontSize: 16, color: C.text1, align: "center", valign: "top", margin: 6, isTextBox: true, objectName: `Beschriftung ${label}` });
});
s.addText("Fälle mit bekannter Sollentscheidung · Familien getrennt nach Split · Texte aus Vorlagen", {
  x: MARGIN, y: 5.2, w: W - 2 * MARGIN, h: 0.5, fontSize: 14, color: GREY, margin: 0, isTextBox: true, objectName: "Hinweis Datensatz" });
s.addNotes("Ohne Beispiele kein Training: Das Modell lernt aus Fällen mit bekannter Sollentscheidung. " +
  "Start mit 5.000 synthetischen Anträgen, später auf 6.000 erweitert. Motive z. B. K11 (Privatkonto, aber geschäftliche Nutzung), K03 (Darlehen statt Einnahmen). " +
  "Grenze: Texte aus Vorlagen.");

// 7 Modell
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Daten und Modell" });
s.addText("Das Modell: Laya Multilingual", { placeholder: "title" });
s.addText("322 Mio.", { x: MARGIN, y: 2.2, w: 4.2, h: 1.2, fontSize: 60, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Parameterzahl" });
s.addText("Parameter · Apache-2.0", { x: MARGIN, y: 3.4, w: 4.2, h: 0.5, fontSize: 16, color: GREY, margin: 0, isTextBox: true, objectName: "Beschriftung Parameter" });
const modelPoints = ["Entscheidungsmodell statt Chatbot", "Lokal trainiert", "Weitere Modelle möglich"];
modelPoints.forEach((t, i) => task(s, t, 5.6, 1.75 + i * 1.35, W - MARGIN - 5.6, 0.95, { align: "left", fontSize: 18 }));
s.addNotes("Entscheidungsmodell statt Chatbot: schnell (80–250 ms), lokal, Apache-2.0; liefert Entscheidung und Wahrscheinlichkeiten, keine Begründung. " +
  "Training auf dem Mac (PyTorch MPS): vorher 246 unnötige Prüfungen von 250, nachher 0. " +
  "Weitere Modelle möglich, z. B. Qwen3.5-4B mit LLM2Jev (größer, kann zusätzlich Text erzeugen) oder andere Laya-Varianten.");

// 7b Anlernen und Nachtrainieren
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Daten und Modell" });
s.addText("Anlernen – und jederzeit wiederholen", { placeholder: "title" });
// Gemessen: 0,45 s je Trainingsfall und Epoche (M1 Max). Hochrechnung: 80 % Training, 3 Epochen.
const trainTimes = [["5.000", "1,6 h", "gemessen"], ["20.000", "6 h", "hochgerechnet"], ["50.000", "15 h", "hochgerechnet"], ["1.000.000", "12 Tage", "1 Epoche: 4 Tage"]];
const tw7 = (W - 2 * MARGIN - 3 * 0.35) / 4, ty7 = 1.55, th7 = 2.2;
trainTimes.forEach(([n, t, sub], i) => {
  const x = MARGIN + i * (tw7 + 0.35);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: ty7, w: tw7, h: th7, rectRadius: 0.12, fill: { color: i === 0 ? LIGHT : "FFFFFF" },
    line: { color: INK, width: 1.5 }, objectName: `Trainingsdauer ${n}` });
  s.addText([
    { text: n, options: { fontSize: 24, bold: true, breakLine: true } },
    { text: "Datensätze", options: { fontSize: 13, color: GREY } },
  ], { x, y: ty7 + 0.2, w: tw7, h: 0.85, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Datensätze ${n}` });
  s.addText([
    { text: t, options: { fontSize: 28, bold: true, breakLine: true } },
    { text: sub, options: { fontSize: 13, color: GREY } },
  ], { x, y: ty7 + 1.15, w: tw7, h: 0.9, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Dauer ${n}` });
});
// Kreislauf: Daten → Training → Prüfung → Einsatz → zurück
const loop = ["Daten ergänzen", "Trainieren", "Prüfen: Test und Gegenproben", "Modell tauschen"];
const lgap = 0.55, lw7 = (W - 2 * MARGIN - 3 * lgap) / 4, ly = 4.3, lh = 0.8;
loop.forEach((t, i) => {
  const x = MARGIN + i * (lw7 + lgap);
  task(s, t, x, ly, lw7, lh, { fontSize: 14, name: `Schritt ${t}` });
  if (i < loop.length - 1) arrow(s, x + lw7, ly + lh / 2, x + lw7 + lgap, ly + lh / 2);
});
const lastMid = MARGIN + 3 * (lw7 + lgap) + lw7 / 2, firstMid = MARGIN + lw7 / 2, back = ly + lh + 0.4;
const plainLine = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
  line: { color: INK, width: 1.5 }, objectName: "Sequenzfluss" });
plainLine(lastMid, ly + lh, lastMid, back);
plainLine(firstMid, back, lastMid, back);
arrow(s, firstMid, back, firstMid, ly + lh);
s.addText("Nachtrainieren ist ein Skriptlauf: neue Fälle rein, Modell raus – der Prozess bleibt unverändert", {
  x: MARGIN + 0.3, y: back + 0.12, w: W - 2 * MARGIN - 0.6, h: 0.4, fontSize: 13, color: GREY, align: "center", margin: 0,
  isTextBox: true, objectName: "Hinweis Kreislauf" });
s.addNotes("Gemessen auf einem Mac M1 Max: 5.000 Datensätze (4.000 Training, 3 Epochen) in 97,6 Minuten; v2 mit 6.000 Datensätzen (2 Epochen) in 66 Minuten. " +
  "Das sind rund 0,45 Sekunden je Trainingsfall und Epoche. Die übrigen Werte sind linear hochgerechnet (80 % Training, 3 Epochen): " +
  "20.000 in etwa 6 Stunden, 50.000 in etwa 15 Stunden – also über Nacht. 1.000.000 bräuchte auf dem Mac rund 12 Tage; " +
  "bei so vielen Daten reicht oft 1 Epoche (rund 4 Tage), sinnvoller ist dann ein GPU-Server (nicht gemessen). " +
  "Wiederholen: Daten ergänzen (augment_dataset.py, Sekunden), trainieren (kyc_train.py), prüfen mit Testsplit und Gegenproben (Minuten), " +
  "dann im Laya-Dienst das Modell tauschen (LAYA_MODEL, Neustart in Sekunden). BPMN und DMN bleiben unverändert. " +
  "Beispiel v2: Die Reeperbahn-Abkürzung wurde mit 1.000 neuen Varianten in gut einer Stunde Training behoben; trainiert wurde ab dem Zwischenstand nach Epoche 1, nicht von vorn.");

// 8 Warum kein großes LLM
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Daten und Modell" });
s.addText("Warum kein großes LLM wie Fable?", { placeholder: "title" });
const reasons = ["Datenschutz", "Kosten und Tempo", "Kontrolle", "Prüfbarkeit"];
const gw = (W - 2 * MARGIN - 0.4) / 2;
reasons.forEach((t, i) => task(s, t, MARGIN + (i % 2) * (gw + 0.4), 1.85 + Math.floor(i / 2) * 2.05, gw, 1.65, { fontSize: 24, bold: true }));
s.addNotes("Datenschutz: Kundendaten gingen an einen externen Dienst – widerspricht Kernaussage 2. " +
  "Kosten und Tempo: pro Antrag Sekunden und Gebühren je Token statt Millisekunden auf eigener Hardware. " +
  "Kontrolle: nicht im eigenen Haus auf die eigene Richtlinie trainierbar, Modellversionen wechseln beim Anbieter. " +
  "Prüfbarkeit: freier Text statt fester Entscheidung mit Wahrscheinlichkeit. " +
  "Fairerweise: Ein großes LLM könnte Begründungen formulieren – das kann Laya nicht.");

// 9 Live-Demo
pres.addSection({ title: "Demo" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Demo" });
s.addText("Live-Demo", { placeholder: "title" });
const demo = [["K01", "Automatische Freigabe"], ["K11", "Geschäftliche Nutzung"], ["K06", "USA-Bezug"], ["K15", "Ablehnung durch Regel"],
  ["K13 / K14", "Wohnadresse vs. Arbeitgeber"], ["", "Postkorb und Dashboard"]];
const dgap = 0.22, dy = 2.6, dh = 1.7;
const dw = (W - 2 * MARGIN - 2 * 0.42 - (demo.length + 1) * dgap) / demo.length;
startEvent(s, MARGIN, dy + dh / 2 - 0.21);
arrow(s, MARGIN + 0.42, dy + dh / 2, MARGIN + 0.42 + dgap, dy + dh / 2);
demo.forEach(([id, label], i) => {
  const x = MARGIN + 0.42 + dgap + i * (dw + dgap);
  s.addText([
    ...(id ? [{ text: id, options: { bold: true, breakLine: true } }] : []),
    { text: label },
  ], { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.12, x, y: dy, w: dw, h: dh, fill: { color: i === demo.length - 1 ? LIGHT : "FFFFFF" },
       line: { color: INK, width: 1.5 }, fontSize: 13, color: C.text1, align: "center", valign: "middle", margin: 4, objectName: `Demo ${id || "Dashboard"}` });
  arrow(s, x + dw, dy + dh / 2, x + dw + dgap, dy + dh / 2);
});
endEvent(s, MARGIN + 0.42 + dgap + demo.length * (dw + dgap), dy + dh / 2 - 0.21);
s.addNotes("K01: automatische Freigabe. K11: Privatkonto mit geplanter Geschäftsnutzung – Laya schickt in die Prüfung. " +
  "K06: Laya sagt ok, Regel R4 erzwingt die Prüfung. K15: bestätigter Sanktionstreffer, R5 lehnt sofort ab – Laya wird gar nicht gefragt. K13/K14: Karl (Wohnadresse Reeperbahn) gegen Marcin (nur Arbeitgeber an der Reeperbahn). " +
  "Danach manuelle Prüfung im Postkorb und Ablauf im Dashboard. Weboberfläche: http://localhost:8080");

// 10 BPMN-Engine
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Demo" });
s.addText("Die BPMN-Engine: Kogito und CIB flow", { placeholder: "title" });
const engines = [
  { logo: LOGO_KOGITO, ratio: 359 / 1279, lw: 2.6, word: null, head: "Für Microservices",
    points: ["BPMN und DMN werden zu Java-Code", "Quarkus-Dienst mit REST-API je Prozess", "Open Source, Apache KIE", "Superschnell", "100% testbar"] },
  { logo: LOGO_CIB, ratio: 1087 / 2400, lw: 1.75, word: "flow", head: "Für die Enterprise-Einbindung",
    points: ["Taskliste und Formulare für User Tasks", "Rechte, Rollen, Konnektoren", "Engine CIB seven (Camunda-7-Fork)"] },
];
const ew = (W - 2 * MARGIN - 0.4) / 2, ey = 1.6, eh = 4.15;
engines.forEach((e, i) => {
  const x = MARGIN + i * (ew + 0.4);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: ey, w: ew, h: eh, rectRadius: 0.12, fill: { color: i === 1 ? LIGHT : "FFFFFF" },
    line: { color: INK, width: 1.5 }, objectName: `Engine ${e.head}` });
  const lh = e.lw * e.ratio;
  s.addImage({ path: e.logo, x: x + 0.4, y: ey + 0.35 + (0.75 - lh) / 2, w: e.lw, h: lh, objectName: `Logo ${e.word ? "CIB flow" : "Kogito"}`,
    altText: e.word ? "Logo CIB" : "Logo Kogito" });
  if (e.word) {
    s.addText(e.word, { x: x + 0.4 + e.lw + 0.15, y: ey + 0.35, w: 1.6, h: 0.75, fontSize: 30, bold: true, color: C.text1,
      valign: "middle", margin: 0, isTextBox: true, objectName: "Schriftzug flow" });
  }
  s.addText(e.head, { x: x + 0.4, y: ey + 1.3, w: ew - 0.8, h: 0.5, fontSize: 20, bold: true, color: C.text1, margin: 0,
    isTextBox: true, objectName: `Einsatz ${e.head}` });
  s.addText(e.points.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < e.points.length - 1 } })), {
    x: x + 0.4, y: ey + 1.95, w: ew - 0.8, h: 2.0, fontSize: 15, color: C.text1, valign: "top", margin: 0,
    paraSpaceAfter: 6, isTextBox: true, objectName: `Merkmale ${e.head}` });
});
quoteBar(s, MARGIN, 5.95, 0.75);
s.addText("Kogito für Microservices – für die Enterprise-Einbindung mit User Tasks empfehlen wir CIB flow.", {
  x: MARGIN + 0.3, y: 5.95, w: W - 2 * MARGIN - 0.3, h: 0.75, fontSize: 16, bold: true, color: C.text1, valign: "middle", margin: 0,
  isTextBox: true, objectName: "Empfehlung" });
s.addNotes("Die Demo läuft auf Kogito 10.2 (Apache KIE) als Quarkus-Microservice: BPMN-Prozess und DMN-Regeln werden beim Build zu Java-Code, " +
  "jeder Prozess bekommt automatisch eine REST-API, der Dienst startet in Sekunden. Ideal, wenn ein Prozess als eigener Dienst in eine Microservice-Landschaft gehört. " +
  "Grenze: Kogito bringt für User Tasks nur eine API mit. Postkorb, Prüfmaske und Dashboard der Demo haben wir selbst gebaut; Rechte, Vertretung und Betrieb fehlen. " +
  "Für die Einbindung im Unternehmen mit vielen Sachbearbeitern empfehlen wir CIB flow: Low-Code-BPM-Plattform der CIB software GmbH mit Taskliste, " +
  "Formularbaukasten (EasyForm), Rechteverwaltung, Dokumenten-Viewer und Konnektoren zu REST-APIs, on-premise oder als SaaS. " +
  "Engine ist CIB seven, ein Fork von Camunda 7. Die Regeln (DMN) und das Laya-Modell lassen sich dort genauso über einen Service-Task anbinden.");

// 10 Fragen
pres.addSection({ title: "Abschluss" });
s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Abschluss" });
s.addText("Fragen?", { placeholder: "title" });
s.addText("Prozesse im Unternehmen · www.piu.de", { placeholder: "body" });
startEvent(s, MARGIN, 5.9);
arrow(s, MARGIN + 0.42, 6.11, MARGIN + 1.1, 6.11);
endEvent(s, MARGIN + 1.1, 5.9);
s.addNotes("15 Minuten Fragerunde.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("geschrieben:", OUT);
})();
