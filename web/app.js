// SkillTalk web client — vanilla JS, no build step.
const $ = (id) => document.getElementById(id);
let session = null;
let sttMode = "browser";
let recorder = null, chunks = [], recognition = null, finalText = "";

async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r;
}

function speak(text) {
  if (!$("speak").checked || !("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.02;
  speechSynthesis.speak(u);
}

function render(turn) {
  session = turn.session_id;
  $("topic").textContent = turn.topic || "";
  $("question").textContent = turn.say;
  $("why").textContent = turn.why ? `Why this matters: ${turn.why}` : "";
  const pct = turn.progress.total ? (100 * turn.progress.covered) / turn.progress.total : 0;
  $("bar").style.width = `${turn.done ? 100 : pct}%`;

  const box = $("options");
  box.innerHTML = "";
  for (const o of turn.options || []) {
    const b = document.createElement("button");
    b.className = "chip";
    b.title = o.explain || "";                     // tooltip
    b.innerHTML = `<span></span><small></small>`;
    b.querySelector("span").textContent = o.label;
    b.querySelector("small").textContent = o.explain ? `(${o.explain})` : "";
    b.onclick = () => send(o.label);
    box.appendChild(b);
  }
  $("transcript").value = "";
  speak(turn.say);

  if (turn.done) finish();
}

async function start() {
  const cfg = await (await api("/api/config")).json();
  sttMode = cfg.stt_provider;
  const turn = await (await api("/api/sessions", { method: "POST" })).json();
  $("start-card").classList.add("hidden");
  $("chat").classList.remove("hidden");
  render(turn);
}

async function send(text) {
  text = (text ?? $("transcript").value).trim();
  if (!text) return status("Say or type an answer first — or tap an option.");
  status("Thinking…");
  try {
    const turn = await (await api(`/api/sessions/${session}/answer`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }),
    })).json();
    status("");
    render(turn);
  } catch (e) { status(`Something went wrong: ${e.message}`); }
}

async function finish() {
  $("result").classList.remove("hidden");
  $("download").href = `/api/sessions/${session}/skill.zip`;
  $("preview").textContent = await (await api(`/api/sessions/${session}/skill`)).text();
  $("result").scrollIntoView({ behavior: "smooth" });
}

function status(msg) { $("status").textContent = msg; }

// ---------- voice input ----------
function startListening() {
  speechSynthesis?.cancel();
  $("mic").classList.add("recording");
  if (sttMode === "browser") {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return status("Your browser has no built-in speech recognition. Try Chrome/Edge, or type.");
    recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    finalText = $("transcript").value ? $("transcript").value + " " : "";
    recognition.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t + " "; else interim += t;
      }
      $("transcript").value = (finalText + interim).trim();
    };
    recognition.start();
    status("Listening… release to stop.");
    return;
  }
  navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => chunks.push(e.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      status("Transcribing…");
      const fd = new FormData();
      fd.append("file", new Blob(chunks, { type: recorder.mimeType }), "answer.webm");
      try {
        const { text } = await (await api(`/api/sessions/${session}/audio`, { method: "POST", body: fd })).json();
        $("transcript").value = [$("transcript").value, text].filter(Boolean).join(" ");
        status("Check the text, then press Send.");
      } catch (e) { status(`Transcription failed: ${e.message}`); }
    };
    recorder.start();
    status("Recording… release to stop.");
  }).catch(() => status("Microphone blocked. Allow mic access in your browser, or type your answer."));
}

function stopListening() {
  $("mic").classList.remove("recording");
  if (recognition) { recognition.stop(); recognition = null; status("Check the text, then press Send."); }
  if (recorder && recorder.state === "recording") recorder.stop();
}

$("start").onclick = start;
$("send").onclick = () => send();
$("mic").addEventListener("pointerdown", startListening);
$("mic").addEventListener("pointerup", stopListening);
$("mic").addEventListener("pointerleave", () => { if ($("mic").classList.contains("recording")) stopListening(); });
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && document.activeElement !== $("transcript") && !e.repeat && session) {
    e.preventDefault(); startListening();
  }
  if (e.key === "Enter" && !e.shiftKey && document.activeElement === $("transcript")) { e.preventDefault(); send(); }
});
document.addEventListener("keyup", (e) => {
  if (e.code === "Space" && document.activeElement !== $("transcript") && session) { e.preventDefault(); stopListening(); }
});
