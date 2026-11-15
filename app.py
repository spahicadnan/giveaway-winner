
import os
import re
import csv
import io
import hmac
import uuid
import secrets
import requests

from flask import Flask, request, jsonify, render_template_string, Response

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
EXPORT_KEY = os.environ.get("EXPORT_KEY")

IG_USER_ID = "17841480659359837"
GRAPH_URL = "https://graph.facebook.com/v27.0"

# Rezultati ostaju zaključani tokom rada aplikacije.
DRAW_SESSIONS = {}


PAGE = r"""
<!DOCTYPE html>
<html lang="bs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Giveaway Winner</title>
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #10101b;
    color: #fff;
    min-height: 100vh;
}

header {
    padding: 24px;
    text-align: center;
    border-bottom: 1px solid #29283b;
}

.logo {
    font-size: 25px;
    font-weight: 800;
    letter-spacing: 1px;
}

.logo span { color: #b68cff; }

.subtitle {
    color: #aaa8bd;
    font-size: 14px;
    margin-top: 8px;
}

.container {
    max-width: 760px;
    margin: 45px auto;
    padding: 20px;
}

.steps {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 35px;
}

.step {
    padding: 10px 16px;
    border-radius: 30px;
    background: #242337;
    color: #9996ad;
    font-size: 13px;
}

.step.active {
    background: #7446bd;
    color: white;
}

.panel {
    background: #1b1a2a;
    border: 1px solid #302e45;
    border-radius: 18px;
    padding: 30px;
    box-shadow: 0 15px 50px #0005;
}

h1 {
    font-size: 27px;
    margin-top: 0;
}

.description {
    color: #aaa8bd;
    line-height: 1.6;
    margin-bottom: 25px;
}

label {
    display: block;
    margin: 18px 0 8px;
    color: #d9d6e8;
    font-size: 14px;
}

input {
    width: 100%;
    padding: 15px;
    border-radius: 9px;
    border: 1px solid #414057;
    background: #11101d;
    color: white;
    font-size: 15px;
    outline: none;
}

input:focus { border-color: #a77aff; }

button {
    border: 0;
    border-radius: 9px;
    padding: 15px 22px;
    background: #8755d5;
    color: white;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    margin-top: 22px;
    width: 100%;
}

button:hover { background: #9a6be5; }
button:disabled { opacity: .5; cursor: wait; }

.secondary {
    background: #302e45;
}

.secondary:hover { background: #403d59; }

.hidden { display: none !important; }

.message {
    margin-top: 18px;
    padding: 13px;
    border-radius: 9px;
    line-height: 1.5;
    display: none;
}

.error {
    display: block;
    background: #49252e;
    color: #ffb9c3;
}

.success {
    display: block;
    background: #1d4539;
    color: #a7f0d2;
}

.stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 22px;
}

.stat {
    background: #11101d;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}

.stat strong {
    display: block;
    font-size: 30px;
    color: #c49aff;
    margin-bottom: 7px;
}

.stat span {
    color: #aaa8bd;
    font-size: 13px;
}

.winner-preview {
    padding: 18px;
    margin-top: 20px;
    background: #302449;
    border: 1px solid #67479b;
    border-radius: 12px;
}

.winner-preview strong {
    color: #d7b8ff;
    font-size: 20px;
}

.presentation {
    max-width: 1100px;
    margin: 0 auto;
    padding: 45px 22px;
    min-height: 85vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
}

.presentation h1 {
    font-size: clamp(30px, 5vw, 54px);
    margin-bottom: 12px;
}

.presentation .intro {
    color: #aaa8bd;
    font-size: 17px;
    margin-bottom: 45px;
}

.winner-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 22px;
}

.winner-card {
    background: linear-gradient(145deg, #25213a, #171625);
    border: 1px solid #51406d;
    border-radius: 20px;
    padding: 38px 15px;
    min-height: 230px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.winner-card .number {
    color: #c29aff;
    font-size: 14px;
    letter-spacing: 3px;
    margin-bottom: 20px;
}

.winner-card .username {
    font-size: clamp(22px, 4vw, 38px);
    font-weight: 800;
    overflow-wrap: anywhere;
}

.winner-card .type {
    color: #aaa8bd;
    font-size: 13px;
    margin-top: 16px;
}

.pending {
    color: #77748c;
    font-size: 22px;
}

.draw-button {
    max-width: 420px;
    margin: 38px auto 0;
    padding: 20px;
    font-size: 17px;
}

.result-info {
    color: #aaa8bd;
    margin-top: 24px;
    line-height: 1.6;
}

.footer {
    color: #77748c;
    text-align: center;
    padding: 25px;
    font-size: 12px;
}

@media(max-width: 600px) {
    .container { margin: 20px auto; }
    .panel { padding: 22px; }
    .winner-grid { grid-template-columns: 1fr; }
    .steps { gap: 5px; }
    .step { padding: 9px; font-size: 11px; }
}
</style>
</head>

<body>

<header>
    <div class="logo">GIVEAWAY <span>WINNER</span></div>
    <div class="subtitle">Transparentno izvlačenje dobitnika</div>
</header>

<div id="setup" class="container">

    <div class="steps">
        <div id="step1" class="step active">1. Prvi pobjednik</div>
        <div id="step2" class="step">2. Instagram objava</div>
    </div>

    <section id="panel1" class="panel">
        <h1>Odaberi prvog pobjednika</h1>
        <p class="description">
            Unesi Instagram korisničko ime osobe koju želiš
            odabrati kao prvog pobjednika. Aplikacija će kasnije
            provjeriti da li je osoba učestvovala u giveawayu.
        </p>

        <label>Instagram username</label>
        <input id="firstWinner" placeholder="@username"
               autocomplete="off">

        <button onclick="goToStep2()">Nastavi</button>
        <div id="message1" class="message"></div>
    </section>

    <section id="panel2" class="panel hidden">
        <h1>Učitaj Instagram komentare</h1>
        <p class="description">
            Unesi link Instagram objave. Aplikacija će automatski
            preuzeti dostupne komentare i pripremiti listu učesnika.
        </p>

        <label>Link Instagram objave</label>
        <input id="postUrl" type="url"
               placeholder="https://www.instagram.com/p/...">

        <label>Export Key</label>
        <input id="exportKey" type="password"
               placeholder="Unesi svoj Export Key">

        <button id="loadButton" onclick="loadComments()">
            Učitaj komentare
        </button>

        <button class="secondary" onclick="backToStep1()">
            Nazad
        </button>

        <div id="message2" class="message"></div>

        <div id="stats" class="hidden">
            <div class="stats">
                <div class="stat">
                    <strong id="commentCount">0</strong>
                    <span>Ukupno komentara</span>
                </div>
                <div class="stat">
                    <strong id="participantCount">0</strong>
                    <span>Jedinstvenih učesnika</span>
                </div>
            </div>

            <div class="winner-preview">
                <div>Prvi pobjednik</div>
                <strong id="previewWinner"></strong>
                <p id="validationText"></p>
            </div>

            <button id="presentationButton"
                    onclick="openPresentation()">
                Otvori glavno izvlačenje
            </button>
        </div>
    </section>
</div>

<section id="presentation" class="presentation hidden">

    <div class="logo">GIVEAWAY <span>WINNER</span></div>

    <h1>Izvlačenje dobitnika</h1>
    <p class="intro">
        Dva pobjednika. Jedan transparentan postupak.
    </p>

    <div class="winner-grid">

        <div class="winner-card">
            <div class="number">POBJEDNIK 01</div>
            <div id="presentationFirst" class="username"></div>
            <div class="type">Ručno odabrani pobjednik</div>
        </div>

        <div class="winner-card">
            <div class="number">POBJEDNIK 02</div>
            <div id="presentationSecond" class="username pending">
                Čeka se izvlačenje...
            </div>
            <div class="type">Nasumično odabrani pobjednik</div>
        </div>

    </div>

    <button id="drawButton" class="draw-button"
            onclick="drawWinner()">
        IZVUCI DRUGOG POBJEDNIKA
    </button>

    <div id="drawInfo" class="result-info">
        Drugi pobjednik bit će izabran nasumično
        među preostalim učesnicima.
    </div>

</section>

<div class="footer">
    Giveaway Winner
</div>

<script>
let firstWinner = "";
let drawId = "";
let exportKey = "";
let drawn = false;

function showMessage(id, text, type) {
    const el = document.getElementById(id);
    el.textContent = text;
    el.className = "message " + type;
}

function goToStep2() {
    const username = document.getElementById("firstWinner")
        .value.trim().replace(/^@/, "").toLowerCase();

    if (!username) {
        showMessage("message1",
            "Unesi Instagram korisničko ime prvog pobjednika.",
            "error");
        return;
    }

    firstWinner = username;

    document.getElementById("panel1").classList.add("hidden");
    document.getElementById("panel2").classList.remove("hidden");

    document.getElementById("step1").classList.remove("active");
    document.getElementById("step2").classList.add("active");
}

function backToStep1() {
    document.getElementById("panel2").classList.add("hidden");
    document.getElementById("panel1").classList.remove("hidden");

    document.getElementById("step2").classList.remove("active");
    document.getElementById("step1").classList.add("active");
}

async function loadComments() {
    const postUrl = document.getElementById("postUrl").value.trim();
    exportKey = document.getElementById("exportKey").value;

    if (!postUrl || !exportKey) {
        showMessage("message2",
            "Unesi link objave i Export Key.",
            "error");
        return;
    }

    const button = document.getElementById("loadButton");
    button.disabled = true;
    button.textContent = "Preuzimanje komentara...";

    document.getElementById("stats").classList.add("hidden");
    document.getElementById("message2").style.display = "none";

    try {
        const response = await fetch("/api/load", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                post_url: postUrl,
                first_winner: firstWinner,
                key: exportKey
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Greška pri učitavanju.");
        }

        drawId = data.draw_id;

        document.getElementById("commentCount").textContent =
            data.comment_count;

        document.getElementById("participantCount").textContent =
            data.participant_count;

        document.getElementById("previewWinner").textContent =
            "@" + firstWinner;

        document.getElementById("validationText").textContent =
            "Potvrđeno: prvi pobjednik nalazi se među učesnicima.";

        document.getElementById("stats").classList.remove("hidden");

        showMessage("message2",
            "Komentari su uspješno učitani. Možeš nastaviti na glavno izvlačenje.",
            "success");

    } catch (error) {
        showMessage("message2", error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Učitaj komentare";
    }
}

function openPresentation() {
    if (!drawId) return;

    document.getElementById("setup").classList.add("hidden");
    document.getElementById("presentation").classList.remove("hidden");

    document.getElementById("presentationFirst").textContent =
        "@" + firstWinner;

    window.scrollTo(0, 0);
}

async function drawWinner() {
    if (!drawId || drawn) return;

    const button = document.getElementById("drawButton");
    const second = document.getElementById("presentationSecond");

    button.disabled = true;
    button.textContent = "IZVLAČENJE U TOKU...";
    second.textContent = "Izvlačenje...";
    second.classList.add("pending");

    document.getElementById("drawInfo").textContent =
        "Sistem bira jednog učesnika nasumično. Molimo sačekajte.";

    try {
        const response = await fetch("/api/draw", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                draw_id: drawId,
                key: exportKey
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Izvlačenje nije uspjelo.");
        }

        // Kratka pauza za vizuelni efekat otkrivanja.
        await new Promise(resolve => setTimeout(resolve, 1800));

        second.classList.remove("pending");
        second.textContent = "@" + data.second_winner;

        button.textContent = "IZVLAČENJE ZAVRŠENO";
        document.getElementById("drawInfo").textContent =
            "Ukupno učesnika: " + data.participant_count +
            " | Prvi pobjednik isključen iz drugog izvlačenja.";

        drawn = true;

    } catch (error) {
        second.textContent = "Greška";
        button.disabled = false;
        button.textContent = "POKUŠAJ PONOVO";
        document.getElementById("drawInfo").textContent =
            error.message;
    }
}
</script>

</body>
</html>
"""


def api_get(endpoint, params=None):
    if not ACCESS_TOKEN:
        raise Exception("Instagram token nije postavljen na Renderu.")

    query = dict(params or {})
    query["access_token"] = ACCESS_TOKEN

    response = requests.get(
        f"{GRAPH_URL}/{endpoint}",
        params=query,
        timeout=40
    )

    try:
        data = response.json()
    except Exception:
        raise Exception("Meta API nije vratio ispravan odgovor.")

    if response.status_code != 200 or "error" in data:
        error = data.get("error", {})
        message = error.get("message", "Meta API greška")
        code = error.get("code", "")
        raise Exception(f"Meta API greška {code}: {message}")

    return data


def get_all_pages(endpoint, params=None):
    results = []
    data = api_get(endpoint, params or {"limit": 100})

    while True:
        results.extend(data.get("data", []))

        next_url = data.get("paging", {}).get("next")

        if not next_url:
            break

        response = requests.get(next_url, timeout=40)

        try:
            data = response.json()
        except Exception:
            raise Exception("Greška pri učitavanju naredne stranice.")

        if response.status_code != 200 or "error" in data:
            error = data.get("error", {})
            raise Exception(
                error.get("message", "Greška pri paginaciji.")
            )

    return results


def extract_shortcode(url):
    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([^/?#]+)",
        url
    )

    if not match:
        raise Exception("Instagram link nije ispravan.")

    return match.group(1)


def normalize_username(username):
    return username.strip().lstrip("@").lower()


def check_key(data):
    supplied = data.get("key", "")

    if not EXPORT_KEY or not hmac.compare_digest(
        str(supplied), EXPORT_KEY
    ):
        return False

    return True


def fetch_participants(post_url):
    shortcode = extract_shortcode(post_url)

    profile = api_get(
        IG_USER_ID,
        {"fields": "id,username"}
    )

    media = get_all_pages(
        f"{IG_USER_ID}/media",
        {
            "fields": "id,permalink,comments_count,timestamp",
            "limit": 100
        }
    )

    target = None

    for item in media:
        try:
            if extract_shortcode(item.get("permalink", "")) == shortcode:
                target = item
                break
        except Exception:
            continue

    if not target:
        raise Exception(
            "Objava nije pronađena na profilu "
            + profile.get("username", "")
            + "."
        )

    comments = get_all_pages(
        f"{target['id']}/comments",
        {
            "fields": "id,text,timestamp,username",
            "limit": 100
        }
    )

    usernames = {}
    missing = 0

    for comment in comments:
        username = comment.get("username", "")

        if not username:
            missing += 1
            continue

        normalized = normalize_username(username)

        if normalized:
            usernames[normalized] = username.lstrip("@")

    if missing:
        raise Exception(
            f"{missing} komentara nema dostupno korisničko ime. "
            "Izvlačenje nije pokrenuto."
        )

    return len(comments), list(usernames.keys())


@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "Giveaway Winner"
    })


@app.route("/api/load", methods=["POST"])
def load_comments():
    data = request.get_json(silent=True) or {}

    if not check_key(data):
        return jsonify({"error": "Neispravan Export Key."}), 403

    try:
        first_winner = normalize_username(
            data.get("first_winner", "")
        )

        if not first_winner:
            return jsonify({
                "error": "Nije unesen prvi pobjednik."
            }), 400

        comment_count, participants = fetch_participants(
            data.get("post_url", "")
        )

        if first_winner not in participants:
            return jsonify({
                "error": (
                    "Prvi pobjednik @" + first_winner
                    + " nije pronađen među učesnicima. "
                    "Provjeri korisničko ime i link objave."
                )
            }), 400

        eligible = [
            username for username in participants
            if username != first_winner
        ]

        if not eligible:
            return jsonify({
                "error": "Nema drugog učesnika za izvlačenje."
            }), 400

        draw_id = uuid.uuid4().hex

        DRAW_SESSIONS[draw_id] = {
            "first_winner": first_winner,
            "participants": participants,
            "eligible": eligible,
            "comment_count": comment_count,
            "second_winner": None
        }

        return jsonify({
            "status": "ok",
            "draw_id": draw_id,
            "comment_count": comment_count,
            "participant_count": len(participants)
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/draw", methods=["POST"])
def draw_winner():
    data = request.get_json(silent=True) or {}

    if not check_key(data):
        return jsonify({"error": "Neispravan Export Key."}), 403

    draw_id = data.get("draw_id", "")
    session = DRAW_SESSIONS.get(draw_id)

    if not session:
        return jsonify({
            "error": "Izvlačenje nije pronađeno. Ponovo učitaj objavu."
        }), 404

    # Ako je već izvučen, uvijek vraćamo isti rezultat.
    if session["second_winner"] is None:
        session["second_winner"] = secrets.choice(
            session["eligible"]
        )

    return jsonify({
        "status": "ok",
        "first_winner": session["first_winner"],
        "second_winner": session["second_winner"],
        "participant_count": len(session["participants"])
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
