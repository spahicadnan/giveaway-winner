
import os
import re
import hmac
import uuid
import secrets
import requests

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
EXPORT_KEY = os.environ.get("EXPORT_KEY")

IG_USER_ID = "17841480659359837"
GRAPH_URL = "https://graph.facebook.com/v27.0"

# Temporary storage. Sessions and verification records disappear
# if the Render service restarts.
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
.container{max-width:650px;margin:55px auto;padding:20px}
.panel{background:#1b1a2a;border:1px solid #302e45;border-radius:20px;padding:32px;box-shadow:0 15px 50px #0005}
h1{font-size:27px;margin-top:0}
.desc{color:#aaa8bd;line-height:1.7;margin-bottom:25px}
label{display:block;margin:19px 0 9px;color:#d9d6e8;font-size:14px}
input{width:100%;padding:15px;border-radius:9px;border:1px solid #414057;background:#11101d;color:white;font-size:15px;outline:none}
input:focus{border-color:#a77aff}
button{width:100%;padding:15px;border:0;border-radius:9px;background:#8755d5;color:#fff;font-size:15px;font-weight:700;cursor:pointer;margin-top:22px}
button:hover{background:#9a6be5}
button:disabled{opacity:.5;cursor:wait}
.message{display:none;margin-top:18px;padding:14px;border-radius:9px;line-height:1.5}
.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#1d4539;color:#a7f0d2}
.footer{text-align:center;color:#77748c;font-size:12px;padding:25px}
</style>
</head>
<body>
<header>
<div class="logo">GIVEAWAY <span>WINNER</span></div>
<div class="sub">Giveaway management</div>
</header>

<div class="container">
<section class="panel">
<h1>Prepare Giveaway</h1>
<p class="desc">
Enter the first winner's Instagram username.
The username will be verified against the participants
when the Instagram comments are loaded on the presentation screen.
</p>

<label>First Winner Username</label>
<input id="firstWinner" placeholder="@username" autocomplete="off">

<label>Export Key</label>
<input id="exportKey" type="password" placeholder="Enter your Export Key">

<button id="continueButton" onclick="createPresentation()">
OPEN PRESENTATION
</button>

<div id="message" class="message"></div>
</section>
</div>

<div class="footer">GIVEAWAY WINNER</div>

<script>
function showMessage(text,type){
 const el=document.getElementById("message");
 el.textContent=text;
 el.className="message "+type;
}

async function createPresentation(){
 const username=document.getElementById("firstWinner").value
  .trim().replace(/^@/,"").toLowerCase();
 const key=document.getElementById("exportKey").value;

 if(!username||!key){
  showMessage("Please enter the username and Export Key.","error");
  return;
 }

 const button=document.getElementById("continueButton");
 button.disabled=true;
 button.textContent="PREPARING...";

 try{
  const response=await fetch("/api/create-session",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({
    first_winner:username,
    key:key
   })
  });

  const data=await response.json();
  if(!response.ok)throw new Error(data.error||"Unable to prepare giveaway.");

  window.open("/presentation/"+data.draw_id,"_blank");
  showMessage("Presentation screen opened successfully.","success");

 }catch(error){
  showMessage(error.message,"error");
 }finally{
  button.disabled=false;
  button.textContent="OPEN PRESENTATION";
 }
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
header{text-align:center;padding:30px 20px 12px}
.logo{font-size:30px;font-weight:900;letter-spacing:3px}
.logo span{color:#c29aff}
.tagline{color:#aaa3bd;font-size:12px;letter-spacing:3px;margin-top:10px;text-transform:uppercase}
.main{max-width:1150px;margin:35px auto;padding:20px;text-align:center}
.eyebrow{color:#d4b4ff;font-size:12px;letter-spacing:5px;text-transform:uppercase;margin-bottom:15px}
h1{font-size:clamp(32px,5vw,57px);margin:0 0 12px;font-weight:900}
.intro{font-size:15px;color:#aaa5b9;margin:0 auto 35px;max-width:650px;line-height:1.6}
.panel{
 max-width:700px;margin:0 auto 30px;text-align:left;
 padding:28px;background:linear-gradient(145deg,#29213b,#191625);
 border:1px solid #60447f;border-radius:20px;
 box-shadow:0 20px 70px #0005;
}
.panel h2{margin:0 0 8px;font-size:22px}
.panel p{color:#aaa5b9;font-size:13px;line-height:1.6;margin:0 0 20px}
label{display:block;color:#d9d0e9;font-size:13px;margin:17px 0 8px}
input,select{
 width:100%;padding:14px;border-radius:9px;
 border:1px solid #49415c;background:#151220;
 color:#fff;font-size:15px;outline:none;
}
input:focus,select:focus{border-color:#b68cff}
button{
 border:0;border-radius:50px;padding:17px 30px;
 background:linear-gradient(110deg,#a9783d,#e0bd80,#a9783d);
 color:#201526;font-size:14px;font-weight:900;
 letter-spacing:1.5px;cursor:pointer;
 box-shadow:0 8px 35px #d0a15b33;
 transition:transform .2s,box-shadow .2s;
}
button:hover{transform:translateY(-2px);box-shadow:0 12px 40px #d0a15b55}
button:disabled{opacity:.55;cursor:wait;transform:none}
.primary{width:100%;margin-top:23px}
.secondary{background:#554071;color:white;box-shadow:none}
.hidden{display:none!important}
.message{display:none;margin-top:15px;padding:13px;border-radius:9px;font-size:13px;line-height:1.5}
.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#1d4539;color:#a7f0d2}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:22px}
.stat{background:#151220;padding:19px 10px;border-radius:12px;text-align:center}
.stat strong{display:block;font-size:30px;color:#d0a6ff;margin-bottom:7px}
.stat span{font-size:11px;color:#aaa5b9;letter-spacing:1px}
.game-title{font-size:20px;font-weight:800;color:#f0d49f;margin-bottom:22px}
.winners{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
.card{
 position:relative;overflow:hidden;min-height:230px;
 display:flex;flex-direction:column;justify-content:center;align-items:center;
 padding:25px 15px;border-radius:20px;
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
.card-label{font-size:12px;letter-spacing:4px;color:#d3b5ff;margin-bottom:25px}
.username{
 font-size:clamp(19px,3vw,34px);font-weight:900;
 overflow-wrap:anywhere;min-height:42px;
 text-shadow:0 0 30px #c39aff55;
}
.username.waiting{color:#c5b6d8}
.card-caption{font-size:10px;letter-spacing:3px;color:#aaa3b9;margin-top:22px}
.card.revealing{animation:pulse 1s ease-in-out infinite alternate;border-color:#c59bff}
@keyframes pulse{
 from{box-shadow:0 15px 45px #0005,0 0 5px #a36be0}
 to{box-shadow:0 15px 55px #0005,0 0 32px #a36be088}
}
.card.revealed{border-color:#d2ad77;box-shadow:0 15px 60px #0005,0 0 35px #d2ad7730}
.card.revealed .card-label{color:#f0cf91}
.draw-area{text-align:center;margin-top:30px}
.status{min-height:25px;margin:20px auto 0;color:#b7a9c8;font-size:13px;letter-spacing:1px}
.verification{
 max-width:600px;margin:30px auto 0;padding:22px;
 background:#211b30;border:1px solid #70518e;border-radius:16px;
}
.verification strong{display:block;font-size:24px;letter-spacing:3px;color:#f0cf91;margin:12px 0}
.verification a{color:#cdaaff;font-size:13px}
.footer{text-align:center;color:#777087;font-size:11px;letter-spacing:3px;padding:40px 15px}
.confetti{position:fixed;top:-20px;width:9px;height:15px;z-index:10;pointer-events:none;animation:fall linear forwards}
@keyframes fall{to{transform:translateY(110vh) rotate(900deg);opacity:.1}}
@media(max-width:700px){
 .main{margin:20px auto}
 .panel{padding:21px}
 .winners{grid-template-columns:1fr}
 .card{min-height:190px}
 .stats{gap:7px}
 .stat strong{font-size:23px}
 .stat span{font-size:9px}
}
</style>
</head>
<body>
<header>
 <div class="logo">GIVEAWAY <span>WINNER</span></div>
 <div class="tagline">The official giveaway experience</div>
</header>

<main class="main">
 <div class="eyebrow">WELCOME TO THE GIVEAWAY</div>
 <h1>Let's find our winners!</h1>
 <p class="intro">
 It's time to discover who will be taking home the prizes.
 Let's get started!
 </p>

 <section class="panel" id="setupPanel">
  <h2>Giveaway Setup</h2>
  <p>Enter the giveaway details to load the participants and start the draw.</p>

  <label>Giveaway Name</label>
  <input id="giveawayName" placeholder="Enter giveaway name">

  <label>Instagram Post URL</label>
  <input id="postUrl" type="url" placeholder="https://www.instagram.com/p/...">

  <label>Number of Winners</label>
  <select id="winnerCount">
   <option value="1">1 Winner</option>
   <option value="2" selected>2 Winners</option>
   <option value="3">3 Winners</option>
   <option value="4">4 Winners</option>
   <option value="5">5 Winners</option>
   <option value="6">6 Winners</option>
   <option value="7">7 Winners</option>
   <option value="8">8 Winners</option>
   <option value="9">9 Winners</option>
   <option value="10">10 Winners</option>
  </select>

  <button class="primary" id="loadButton" onclick="loadParticipants()">
   LOAD PARTICIPANTS
  </button>
  <div id="loadMessage" class="message"></div>

  <div id="stats" class="hidden">
   <div class="stats">
    <div class="stat">
     <strong id="commentCount">0</strong>
     <span>TOTAL COMMENTS</span>
    </div>
    <div class="stat">
     <strong id="participantCount">0</strong>
     <span>UNIQUE USERS</span>
    </div>
    <div class="stat">
     <strong id="winnerTotal">0</strong>
     <span>WINNERS</span>
    </div>
   </div>
  </div>
 </section>

 <section id="drawPanel" class="hidden">
  <div class="game-title" id="displayGiveawayName"></div>
  <div class="winners" id="winnerCards"></div>

  <div class="draw-area">
   <button id="drawButton" onclick="revealWinners()">
    START THE DRAW
   </button>
   <div class="status" id="status">
    All participants are ready. Good luck!
   </div>
  </div>

  <div id="verification" class="verification hidden">
   <div class="card-label">RESULT VERIFICATION CODE</div>
   <strong id="verificationCode"></strong>
   <a href="/verify" target="_blank">Verify these results</a>
  </div>
 </section>
</main>

<div class="footer">GIVEAWAY WINNER</div>

<script>
const DRAW_ID = {{ draw_id|tojson }};
let participants = [];
let loaded = false;
let completed = false;
let animationTimers = [];

function showMessage(id,text,type){
 const el=document.getElementById(id);
 el.textContent=text;
 el.className="message "+type;
}

function sleep(ms){
 return new Promise(resolve=>setTimeout(resolve,ms));
}

async function loadParticipants(){
 const name=document.getElementById("giveawayName").value.trim();
 const postUrl=document.getElementById("postUrl").value.trim();
 const winnerCount=Number(document.getElementById("winnerCount").value);

 if(!name||!postUrl){
  showMessage("loadMessage","Please enter the giveaway name and Instagram post URL.","error");
  return;
 }

 const button=document.getElementById("loadButton");
 button.disabled=true;
 button.textContent="LOADING PARTICIPANTS...";

 try{
  const response=await fetch("/api/load",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({
    draw_id:DRAW_ID,
    giveaway_name:name,
    post_url:postUrl,
    winner_count:winnerCount
   })
  });

  const data=await response.json();
  if(!response.ok)throw new Error(data.error||"Unable to load participants.");

  participants=data.participants;
  loaded=true;

  document.getElementById("commentCount").textContent=data.comment_count;
  document.getElementById("participantCount").textContent=data.participant_count;
  document.getElementById("winnerTotal").textContent=data.winner_count;
  document.getElementById("displayGiveawayName").textContent=name;

  document.getElementById("stats").classList.remove("hidden");
  document.getElementById("drawPanel").classList.remove("hidden");

  createWinnerCards(data.winner_count);

  document.getElementById("setupPanel").classList.add("hidden");
  document.getElementById("drawPanel").scrollIntoView({behavior:"smooth"});

 }catch(error){
  showMessage("loadMessage",error.message,"error");
 }finally{
  button.disabled=false;
  button.textContent="LOAD PARTICIPANTS";
 }
}

function createWinnerCards(count){
 const container=document.getElementById("winnerCards");
 container.innerHTML="";

 for(let i=0;i<count;i++){
  const card=document.createElement("div");
  card.className="card";
  card.id="card"+i;

  const label=document.createElement("div");
  label.className="card-label";
  label.textContent="WINNER #"+(i+1);

  const username=document.createElement("div");
  username.className="username waiting";
  username.id="winner"+i;
  username.textContent="?";

  const caption=document.createElement("div");
  caption.className="card-caption";
  caption.textContent="GIVEAWAY WINNER";

  card.append(label,username,caption);
  container.appendChild(card);
 }
}

function confetti(){
 const symbols=["✦","●","◆"];
 for(let i=0;i<130;i++){
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
 if(completed||!loaded)return;

 const button=document.getElementById("drawButton");
 const status=document.getElementById("status");
 const count=Number(document.getElementById("winnerCount").value);

 button.disabled=true;
 button.textContent="DRAW IN PROGRESS...";
 status.textContent="Good luck to all participants!";

 const cards=[];
 const names=[];

 for(let i=0;i<count;i++){
  cards.push(document.getElementById("card"+i));
  names.push(document.getElementById("winner"+i));
  cards[i].classList.add("revealing");
  names[i].classList.remove("waiting");
 }

 let result;

 try{
  const response=await fetch("/api/draw",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({draw_id:DRAW_ID})
  });

  result=await response.json();
  if(!response.ok)throw new Error(result.error||"The draw could not be completed.");

  // Cycle through the actual usernames on every winner card.
  const start=Date.now();
  let index=0;

  while(Date.now()-start<6500){
   for(let i=0;i<count;i++){
    names[i].textContent="@"+participants[(index+i*7)%participants.length];
   }
   index=(index+1)%participants.length;
   await sleep(90);
  }

  // Reveal all winners at the same time.
  result.winners.forEach((winner,i)=>{
   names[i].textContent="@"+winner;
  });

  cards.forEach(card=>{
   card.classList.remove("revealing");
   card.classList.add("revealed");
  });

  status.textContent="Congratulations to all our winners!";
  button.textContent="WINNERS ANNOUNCED";
  completed=true;

  document.getElementById("verificationCode").textContent=result.verification_code;
  document.getElementById("verification").classList.remove("hidden");

  confetti();

 }catch(error){
  cards.forEach((card,i)=>{
   card.classList.remove("revealing");
   names[i].textContent="?";
   names[i].classList.add("waiting");
  });

  status.textContent=error.message;
  button.disabled=false;
  button.textContent="TRY AGAIN";
 }
}
</script>
</body>
</html>
"""


VERIFY_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Giveaway Winner | Verification</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;min-height:100vh;background:linear-gradient(145deg,#11101d,#211832);
 color:#fff;font-family:Arial,sans-serif;
 display:flex;align-items:center;justify-content:center;padding:20px;
}
.panel{
 width:100%;max-width:620px;padding:35px;
 background:#1b1a2a;border:1px solid #51406b;border-radius:20px;
 box-shadow:0 20px 70px #0006;
}
.logo{text-align:center;font-size:25px;font-weight:900;letter-spacing:2px;margin-bottom:10px}
.logo span{color:#b68cff}
.sub{text-align:center;color:#aaa5b9;font-size:13px;margin-bottom:30px}
h1{text-align:center;font-size:25px}
label{display:block;margin:20px 0 8px;color:#d9d6e8;font-size:14px}
input{
 width:100%;padding:16px;border-radius:9px;
 border:1px solid #49415c;background:#11101d;color:#fff;font-size:17px;
}
button{
 width:100%;margin-top:18px;padding:16px;border:0;border-radius:9px;
 background:#8755d5;color:white;font-size:14px;font-weight:800;cursor:pointer;
}
.message{display:none;margin-top:18px;padding:14px;border-radius:9px;line-height:1.5}
.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#1d4539;color:#a7f0d2}
.results{margin-top:25px}
.result-item{padding:14px;margin-top:10px;border-radius:10px;background:#11101d}
.result-item span{display:block;color:#aaa5b9;font-size:11px;margin-bottom:7px}
.result-item strong{font-size:18px;overflow-wrap:anywhere}
.status{margin-top:18px;color:#a7f0d2;font-size:13px;text-align:center}
</style>
</head>
<body>
<div class="panel">
 <div class="logo">GIVEAWAY <span>WINNER</span></div>
 <div class="sub">Official result verification</div>
 <h1>Verify Giveaway Results</h1>

 <label>Verification Code</label>
 <input id="code" placeholder="GW-XXXXXX" autocomplete="off">

 <button id="verifyButton" onclick="verifyCode()">VERIFY RESULTS</button>
 <div id="message" class="message"></div>
 <div id="results" class="results"></div>
</div>

<script>
function showMessage(text,type){
 const el=document.getElementById("message");
 el.textContent=text;
 el.className="message "+type;
}

async function verifyCode(){
 const code=document.getElementById("code").value.trim();
 const button=document.getElementById("verifyButton");
 const results=document.getElementById("results");
 results.innerHTML="";

 if(!code){
  showMessage("Please enter a verification code.","error");
  return;
 }

 button.disabled=true;
 button.textContent="VERIFYING...";

 try{
  const response=await fetch("/api/verify",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({code:code})
  });

  const data=await response.json();
  if(!response.ok)throw new Error(data.error||"Verification failed.");

  const fields=[
   ["Giveaway Name",data.giveaway_name],
   ["Instagram Post",data.post_url],
   ["Date and Time",data.created_at],
   ["Total Comments",data.comment_count],
   ["Unique Participants",data.participant_count],
   ["Number of Winners",data.winner_count]
  ];

  fields.forEach(([label,value])=>{
   const item=document.createElement("div");
   item.className="result-item";
   const span=document.createElement("span");
   span.textContent=label;
   const strong=document.createElement("strong");
   strong.textContent=value;
   item.append(span,strong);
   results.appendChild(item);
  });

  data.winners.forEach((winner,index)=>{
   const item=document.createElement("div");
   item.className="result-item";
   const span=document.createElement("span");
   span.textContent="WINNER #"+(index+1);
   const strong=document.createElement("strong");
   strong.textContent="@"+winner;
   item.append(span,strong);
   results.appendChild(item);
  });

  showMessage("Verification successful. These are the recorded results.","success");

 }catch(error){
  showMessage(error.message,"error");
 }finally{
  button.disabled=false;
  button.textContent="VERIFY RESULTS";
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
        raise Exception(error.get("message", "Meta API error"))

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
            raise Exception(error.get("message", "Pagination error."))

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


def generate_verification_code():
    existing = {
        session.get("verification_code")
        for session in DRAW_SESSIONS.values()
    }

    while True:
        code = "GW-" + secrets.token_hex(3).upper()
        if code not in existing:
            return code


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


@app.route("/verify")
def verify_page():
    return render_template_string(VERIFY_PAGE)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "Giveaway Winner"
    })


@app.route("/api/create-session", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}

    if not check_key(data):
        return jsonify({"error": "Invalid Export Key."}), 403

    first_winner = normalize_username(
        data.get("first_winner", "")
    )

    if not first_winner:
        return jsonify({
            "error": "First winner username is required."
        }), 400

    draw_id = uuid.uuid4().hex

    DRAW_SESSIONS[draw_id] = {
        "first_winner": first_winner,
        "participants": [],
        "eligible": [],
        "comment_count": 0,
        "giveaway_name": "",
        "post_url": "",
        "winner_count": 0,
        "winners": None,
        "verification_code": None,
        "created_at": None
    }

    return jsonify({
        "status": "ok",
        "draw_id": draw_id
    })


@app.route("/api/load", methods=["POST"])
def load_comments():
    data = request.get_json(silent=True) or {}
    draw_id = data.get("draw_id", "")

    session = DRAW_SESSIONS.get(draw_id)

    if not session:
        return jsonify({
            "error": "Presentation session not found. Please start again."
        }), 404

    if session["winners"] is not None:
        return jsonify({
            "error": "This giveaway has already been completed."
        }), 400

    giveaway_name = str(data.get("giveaway_name", "")).strip()
    post_url = str(data.get("post_url", "")).strip()

    try:
        winner_count = int(data.get("winner_count", 0))
    except (TypeError, ValueError):
        winner_count = 0

    if not giveaway_name or not post_url:
        return jsonify({
            "error": "Giveaway name and Instagram URL are required."
        }), 400

    if winner_count < 1 or winner_count > 10:
        return jsonify({
            "error": "Choose between 1 and 10 winners."
        }), 400

    try:
        comment_count, usernames = fetch_participants(post_url)

        first_winner = session["first_winner"]

        if first_winner not in usernames:
            return jsonify({
                "error": (
                    "The selected first winner was not found "
                    "among the participants. Please check the username."
                )
            }), 400

        if winner_count > len(usernames):
            return jsonify({
                "error": "There are not enough unique participants."
            }), 400

        eligible = [
            username
            for normalized, username in usernames.items()
            if normalized != first_winner
        ]

        session["participants"] = list(usernames.values())
        session["eligible"] = eligible
        session["comment_count"] = comment_count
        session["giveaway_name"] = giveaway_name
        session["post_url"] = post_url
        session["winner_count"] = winner_count

        return jsonify({
            "status": "ok",
            "comment_count": comment_count,
            "participant_count": len(usernames),
            "winner_count": winner_count,
            "participants": list(usernames.values())
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/draw", methods=["POST"])
def draw_winners():
    data = request.get_json(silent=True) or {}
    draw_id = data.get("draw_id", "")

    session = DRAW_SESSIONS.get(draw_id)

    if not session:
        return jsonify({
            "error": "Draw not found. Please load the post again."
        }), 404

    if not session["participants"]:
        return jsonify({
            "error": "Participants have not been loaded."
        }), 400

    if session["winners"] is None:
        additional_count = session["winner_count"] - 1

        additional_winners = secrets.SystemRandom().sample(
            session["eligible"],
            additional_count
        )

        session["winners"] = [
            session["participants"][
                next(
                    i for i, username in enumerate(session["participants"])
                    if normalize_username(username) == session["first_winner"]
                )
            ]
        ] + additional_winners

        session["verification_code"] = generate_verification_code()

        from datetime import datetime, timezone
        session["created_at"] = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

    return jsonify({
        "status": "ok",
        "winners": session["winners"],
        "verification_code": session["verification_code"]
    })


@app.route("/api/verify", methods=["POST"])
def verify_results():
    data = request.get_json(silent=True) or {}
    supplied_code = str(data.get("code", "")).strip().upper()

    if not supplied_code:
        return jsonify({"error": "Please enter a verification code."}), 400

    for session in DRAW_SESSIONS.values():
        saved_code = session.get("verification_code")

        if saved_code and hmac.compare_digest(
            supplied_code,
            saved_code
        ):
            return jsonify({
                "status": "verified",
                "giveaway_name": session["giveaway_name"],
                "post_url": session["post_url"],
                "created_at": session["created_at"],
                "comment_count": session["comment_count"],
                "participant_count": len(session["participants"]),
                "winner_count": session["winner_count"],
                "winners": session["winners"]
            })

    return jsonify({
        "error": "Verification code not found or session has expired."
    }), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
