
import os
import re
import hmac
import uuid
import secrets
import requests

from flask import (
    Flask, request, jsonify, render_template_string
)

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
EXPORT_KEY = os.environ.get("EXPORT_KEY")

IG_USER_ID = "17841480659359837"
GRAPH_URL = "https://graph.facebook.com/v27.0"

DRAW_SESSIONS = {}


ADMIN_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Giveaway Winner | Admin</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#10101b;color:#fff;font-family:Arial,sans-serif;min-height:100vh}
header{text-align:center;padding:30px 20px;border-bottom:1px solid #29283b}
.logo{font-size:27px;font-weight:900;letter-spacing:2px}
.logo span{color:#b68cff}
.sub{color:#9996ad;font-size:13px;margin-top:9px}
.container{max-width:700px;margin:55px auto;padding:20px}
.steps{display:flex;justify-content:center;gap:12px;margin-bottom:30px}
.step{padding:10px 17px;border-radius:30px;background:#242337;color:#9996ad;font-size:13px}
.step.active{background:#7446bd;color:#fff}
.panel{background:#1b1a2a;border:1px solid #302e45;border-radius:20px;padding:32px;box-shadow:0 15px 50px #0005}
h1{font-size:27px;margin-top:0}
.desc{color:#aaa8bd;line-height:1.7;margin-bottom:25px}
label{display:block;margin:19px 0 9px;color:#d9d6e8;font-size:14px}
input{width:100%;padding:15px;border-radius:9px;border:1px solid #414057;background:#11101d;color:white;font-size:15px;outline:none}
input:focus{border-color:#a77aff}
button{width:100%;padding:15px;border:0;border-radius:9px;background:#8755d5;color:#fff;font-size:15px;font-weight:700;cursor:pointer;margin-top:22px}
button:hover{background:#9a6be5}
button:disabled{opacity:.5;cursor:wait}
.secondary{background:#302e45}
.message{display:none;margin-top:18px;padding:14px;border-radius:9px;line-height:1.5}
.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#1d4539;color:#a7f0d2}
.hidden{display:none!important}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:22px}
.stat{background:#11101d;padding:20px;border-radius:12px;text-align:center}
.stat strong{display:block;font-size:30px;color:#c49aff;margin-bottom:7px}
.stat span{font-size:13px;color:#aaa8bd}
.winner-preview{padding:18px;margin-top:20px;background:#302449;border:1px solid #67479b;border-radius:12px}
.winner-preview strong{display:block;color:#d7b8ff;font-size:20px;margin-top:8px}
.footer{text-align:center;color:#77748c;font-size:12px;padding:25px}
@media(max-width:600px){.container{margin:20px auto}.panel{padding:22px}.steps{gap:5px}.step{padding:9px;font-size:11px}}
</style>
</head>
<body>
<header>
<div class="logo">GIVEAWAY <span>WINNER</span></div>
<div class="sub">Giveaway management</div>
</header>

<div class="container">
<div class="steps">
<div id="step1" class="step active">01 · First Winner</div>
<div id="step2" class="step">02 · Instagram Post</div>
</div>

<section id="panel1" class="panel">
<h1>Select First Winner</h1>
<p class="desc">
Enter the Instagram username of your selected winner.
Their participation will be verified against the comments
before the draw can continue.
</p>
<label>Instagram Username</label>
<input id="firstWinner" placeholder="@username" autocomplete="off">
<button onclick="goToStep2()">Continue</button>
<div id="message1" class="message"></div>
</section>

<section id="panel2" class="panel hidden">
<h1>Import Instagram Comments</h1>
<p class="desc">
Enter the Instagram post URL. The system will retrieve
the available comments and prepare the participant list.
</p>
<label>Instagram Post URL</label>
<input id="postUrl" type="url" placeholder="https://www.instagram.com/p/...">
<label>Export Key</label>
<input id="exportKey" type="password" placeholder="Enter your Export Key">

<button id="loadButton" onclick="loadComments()">Load Comments</button>
<button class="secondary" onclick="backToStep1()">Back</button>

<div id="message2" class="message"></div>

<div id="stats" class="hidden">
<div class="stats">
<div class="stat"><strong id="commentCount">0</strong><span>Total Comments</span></div>
<div class="stat"><strong id="participantCount">0</strong><span>Unique Participants</span></div>
</div>
<div class="winner-preview">
<div>First Winner Verified</div>
<strong id="previewWinner"></strong>
</div>
<button onclick="openPresentation()">Open Presentation Screen</button>
</div>
</section>
</div>
<div class="footer">GIVEAWAY WINNER</div>

<script>
let firstWinner = "";
let drawId = "";
let exportKey = "";

function showMessage(id,text,type){
 const el=document.getElementById(id);
 el.textContent=text;
 el.className="message "+type;
}

function goToStep2(){
 const username=document.getElementById("firstWinner").value
 .trim().replace(/^@/,"").toLowerCase();

 if(!username){
  showMessage("message1","Please enter an Instagram username.","error");
  return;
 }

 firstWinner=username;
 document.getElementById("panel1").classList.add("hidden");
 document.getElementById("panel2").classList.remove("hidden");
 document.getElementById("step1").classList.remove("active");
 document.getElementById("step2").classList.add("active");
}

function backToStep1(){
 document.getElementById("panel2").classList.add("hidden");
 document.getElementById("panel1").classList.remove("hidden");
 document.getElementById("step2").classList.remove("active");
 document.getElementById("step1").classList.add("active");
}

async function loadComments(){
 const postUrl=document.getElementById("postUrl").value.trim();
 exportKey=document.getElementById("exportKey").value;

 if(!postUrl||!exportKey){
  showMessage("message2","Please enter the post URL and Export Key.","error");
  return;
 }

 const button=document.getElementById("loadButton");
 button.disabled=true;
 button.textContent="Loading comments...";
 document.getElementById("stats").classList.add("hidden");

 try{
  const response=await fetch("/api/load",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({
    post_url:postUrl,
    first_winner:firstWinner,
    key:exportKey
   })
  });

  const data=await response.json();
  if(!response.ok) throw new Error(data.error||"Unable to load comments.");

  drawId=data.draw_id;
  document.getElementById("commentCount").textContent=data.comment_count;
  document.getElementById("participantCount").textContent=data.participant_count;
  document.getElementById("previewWinner").textContent="@"+firstWinner;
  document.getElementById("stats").classList.remove("hidden");

  showMessage("message2","Comments successfully imported. The first winner has been verified.","success");

 }catch(error){
  showMessage("message2",error.message,"error");
 }finally{
  button.disabled=false;
  button.textContent="Load Comments";
 }
}

function openPresentation(){
 if(!drawId)return;
 window.open("/presentation/"+drawId,"_blank");
}
</script>
</body>
</html>
"""


PRESENTATION_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Giveaway Winner | Live Draw</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;min-height:100vh;overflow-x:hidden;
 background:
 radial-gradient(ellipse at 50% 0%,#35214f 0%,transparent 48%),
 linear-gradient(145deg,#11101d,#171326 55%,#100f19);
 color:#fff;font-family:Arial,sans-serif;
}
header{text-align:center;padding:35px 20px 15px}
.logo{font-size:30px;font-weight:900;letter-spacing:3px}
.logo span{color:#c29aff}
.tagline{color:#aaa3bd;font-size:13px;letter-spacing:3px;margin-top:12px;text-transform:uppercase}
.main{max-width:1150px;margin:55px auto 30px;padding:20px;text-align:center}
.eyebrow{color:#d4b4ff;font-size:13px;letter-spacing:5px;text-transform:uppercase;margin-bottom:18px}
h1{font-size:clamp(34px,5vw,62px);margin:0 0 15px;font-weight:900;letter-spacing:-1px}
.intro{font-size:16px;color:#aaa5b9;margin:0 auto 55px;max-width:600px;line-height:1.6}
.winners{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.card{
 position:relative;overflow:hidden;min-height:310px;
 display:flex;flex-direction:column;justify-content:center;align-items:center;
 padding:35px 20px;border-radius:24px;
 background:linear-gradient(145deg,#29213b,#191625);
 border:1px solid #6a4b8b;
 box-shadow:0 20px 70px #0005;
}
.card:before{
 content:"";position:absolute;inset:0;
 background:linear-gradient(110deg,transparent 25%,#ffffff0b 50%,transparent 75%);
 transform:translateX(-120%);
}
.card.revealing:before{animation:shine 1.1s linear infinite}
@keyframes shine{to{transform:translateX(120%)}}
.card-label{font-size:13px;letter-spacing:5px;color:#d3b5ff;margin-bottom:27px}
.username{
 font-size:clamp(23px,3.8vw,43px);font-weight:900;
 overflow-wrap:anywhere;min-height:55px;
 text-shadow:0 0 30px #c39aff55;
}
.username.waiting{color:#c5b6d8;letter-spacing:8px}
.card-caption{font-size:12px;letter-spacing:3px;color:#aaa3b9;margin-top:25px}
.card.revealing{animation:pulse 1s ease-in-out infinite alternate;border-color:#c59bff}
@keyframes pulse{
 from{box-shadow:0 15px 45px #0005,0 0 5px #a36be0}
 to{box-shadow:0 15px 55px #0005,0 0 32px #a36be088}
}
.card.revealed{border-color:#d2ad77;box-shadow:0 15px 60px #0005,0 0 35px #d2ad7730}
.card.revealed .card-label{color:#f0cf91}
button{
 display:block;margin:45px auto 0;padding:20px 42px;
 border:1px solid #e0bd80;border-radius:50px;
 background:linear-gradient(110deg,#a9783d,#e0bd80,#a9783d);
 color:#201526;font-size:15px;font-weight:900;
 letter-spacing:2px;cursor:pointer;
 box-shadow:0 8px 35px #d0a15b33;
 transition:transform .2s,box-shadow .2s;
}
button:hover{transform:translateY(-3px);box-shadow:0 12px 40px #d0a15b55}
button:disabled{opacity:.65;cursor:wait;transform:none}
.status{min-height:28px;margin:25px auto 0;color:#b7a9c8;font-size:14px;letter-spacing:1px}
.footer{text-align:center;color:#777087;font-size:11px;letter-spacing:3px;padding:45px 15px}
.confetti{position:fixed;top:-20px;width:9px;height:15px;z-index:10;pointer-events:none;animation:fall linear forwards}
@keyframes fall{to{transform:translateY(110vh) rotate(900deg);opacity:.1}}
@media(max-width:700px){
 .main{margin:25px auto}
 .winners{grid-template-columns:1fr;gap:17px}
 .card{min-height:230px}
 .intro{margin-bottom:35px}
}
</style>
</head>
<body>
<header>
 <div class="logo">GIVEAWAY <span>WINNER</span></div>
 <div class="tagline">The official winner announcement</div>
</header>

<main class="main">
 <div class="eyebrow">The moment we've been waiting for</div>
 <h1>And the winners are...</h1>
 <p class="intro">
 Two winners. One exciting moment.
 Thank you to everyone who participated!
 </p>

 <div class="winners">
  <div class="card" id="card1">
   <div class="card-label">WINNER #1</div>
   <div class="username waiting" id="winner1">?</div>
   <div class="card-caption">GIVEAWAY WINNER</div>
  </div>

  <div class="card" id="card2">
   <div class="card-label">WINNER #2</div>
   <div class="username waiting" id="winner2">?</div>
   <div class="card-caption">GIVEAWAY WINNER</div>
  </div>
 </div>

 <button id="revealButton" onclick="revealWinners()">
  REVEAL THE WINNERS
 </button>

 <div class="status" id="status">
  Get ready. The winners will be revealed together.
 </div>
</main>

<div class="footer">GIVEAWAY WINNER</div>

<script>
const DRAW_ID = {{ draw_id|tojson }};
let completed = false;

function sleep(ms){
 return new Promise(resolve=>setTimeout(resolve,ms));
}

function confetti(){
 const symbols=["✦","●","◆"];
 for(let i=0;i<100;i++){
  const piece=document.createElement("div");
  piece.className="confetti";
  piece.textContent=symbols[Math.floor(Math.random()*symbols.length)];
  piece.style.left=Math.random()*100+"vw";
  piece.style.color=["#e9c77e","#c59bff","#ffffff","#a9e7d0"][Math.floor(Math.random()*4)];
  piece.style.fontSize=(8+Math.random()*13)+"px";
  piece.style.animationDuration=(2.5+Math.random()*3)+"s";
  piece.style.animationDelay=(Math.random()*1.2)+"s";
  document.body.appendChild(piece);
  setTimeout(()=>piece.remove(),6500);
 }
}

async function revealWinners(){
 if(completed)return;

 const button=document.getElementById("revealButton");
 const status=document.getElementById("status");
 const card1=document.getElementById("card1");
 const card2=document.getElementById("card2");
 const name1=document.getElementById("winner1");
 const name2=document.getElementById("winner2");

 button.disabled=true;
 button.textContent="DRAW IN PROGRESS...";
 status.textContent="Selecting the winners...";

 card1.classList.add("revealing");
 card2.classList.add("revealing");
 name1.classList.remove("waiting");
 name2.classList.remove("waiting");

 let result;

 try{
  const response=await fetch("/api/draw",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({draw_id:DRAW_ID})
  });

  result=await response.json();
  if(!response.ok)throw new Error(result.error||"The draw could not be completed.");

  // Both cards animate together before the results are revealed.
  const start=Date.now();
  while(Date.now()-start<4200){
   name1.textContent="✦ ✦ ✦";
   name2.textContent="✦ ✦ ✦";
   await sleep(180);
   name1.textContent="DRAWING";
   name2.textContent="DRAWING";
   await sleep(180);
  }

  name1.textContent="@"+result.first_winner;
  name2.textContent="@"+result.second_winner;

  card1.classList.remove("revealing");
  card2.classList.remove("revealing");
  card1.classList.add("revealed");
  card2.classList.add("revealed");

  status.textContent="Congratulations to both winners!";
  button.textContent="WINNERS ANNOUNCED";
  completed=true;
  confetti();

 }catch(error){
  card1.classList.remove("revealing");
  card2.classList.remove("revealing");
  name1.textContent="?";
  name2.textContent="?";
  name1.classList.add("waiting");
  name2.classList.add("waiting");
  status.textContent=error.message;
  button.disabled=false;
  button.textContent="TRY AGAIN";
 }
}
</script>
</body>
</html>
"""


def api_get(endpoint, params=None):
    if not ACCESS_TOKEN:
        raise Exception("Instagram token is not configured.")

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
        raise Exception("Invalid response from Meta API.")

    if response.status_code != 200 or "error" in data:
        error = data.get("error", {})
        raise Exception(
            error.get("message", "Meta API error")
        )

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
        data = response.json()

        if response.status_code != 200 or "error" in data:
            error = data.get("error", {})
            raise Exception(
                error.get("message", "Pagination error.")
            )

    return results


def extract_shortcode(url):
    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([^/?#]+)",
        url
    )

    if not match:
        raise Exception("Invalid Instagram post URL.")

    return match.group(1)


def normalize_username(username):
    return username.strip().lstrip("@").lower()


def check_key(data):
    supplied = str(data.get("key", ""))

    return bool(
        EXPORT_KEY and
        hmac.compare_digest(supplied, EXPORT_KEY)
    )


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
            "Post not found on Instagram account "
            + profile.get("username", "")
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
            f"{missing} comments did not include a username. "
            "The draw cannot continue."
        )

    return len(comments), usernames


@app.route("/")
def home():
    return render_template_string(ADMIN_PAGE)


@app.route("/presentation/<draw_id>")
def presentation(draw_id):
    if draw_id not in DRAW_SESSIONS:
        return "This presentation link is invalid or has expired.", 404

    return render_template_string(
        PRESENTATION_PAGE,
        draw_id=draw_id
    )


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
        return jsonify({"error": "Invalid Export Key."}), 403

    try:
        first_winner = normalize_username(
            data.get("first_winner", "")
        )

        if not first_winner:
            return jsonify({
                "error": "First winner username is required."
            }), 400

        comment_count, usernames = fetch_participants(
            data.get("post_url", "")
        )

        if first_winner not in usernames:
            return jsonify({
                "error": (
                    "The selected first winner was not found "
                    "among the participants. Check the username."
                )
            }), 400

        eligible = [
            username for username in usernames
            if username != first_winner
        ]

        if not eligible:
            return jsonify({
                "error": "There are not enough participants."
            }), 400

        draw_id = uuid.uuid4().hex

        DRAW_SESSIONS[draw_id] = {
            "first_winner": usernames[first_winner],
            "second_winner": None,
            "participants": list(usernames.values()),
            "eligible": [
                usernames[username] for username in eligible
            ],
            "comment_count": comment_count
        }

        return jsonify({
            "status": "ok",
            "draw_id": draw_id,
            "comment_count": comment_count,
            "participant_count": len(usernames)
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/draw", methods=["POST"])
def draw_winner():
    data = request.get_json(silent=True) or {}
    draw_id = data.get("draw_id", "")

    session = DRAW_SESSIONS.get(draw_id)

    if not session:
        return jsonify({
            "error": "Draw not found. Please load the post again."
        }), 404

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
