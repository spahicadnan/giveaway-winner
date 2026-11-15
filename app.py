import os
import re
import hmac
import uuid
import secrets
import requests

from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
EXPORT_KEY = os.environ.get("EXPORT_KEY")

IG_USER_ID = "17841480659359837"
GRAPH_URL = "https://graph.facebook.com/v27.0"

# Temporary storage: sessions and verification records disappear
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
      The username will be checked against the participants
      when comments are loaded on the presentation screen.
    </p>
    <label for="firstWinner">First Winner Username</label>
    <input id="firstWinner" placeholder="@username" autocomplete="off">
    <label for="exportKey">Export Key</label>
    <input id="exportKey" type="password" placeholder="Enter your Export Key">
    <button id="continueButton" onclick="createPresentation()">OPEN PRESENTATION</button>
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
  const username=document.getElementById("firstWinner").value.trim().replace(/^@/,"").toLowerCase();
  const key=document.getElementById("exportKey").value;
  if(!username||!key){showMessage("Please enter the username and Export Key.","error");return;}

  // Open the tab immediately so the browser does not block it after fetch().
  const presentationTab=window.open("about:blank","_blank");
  if(!presentationTab){showMessage("Please allow pop-ups and try again.","error");return;}

  const button=document.getElementById("continueButton");
  button.disabled=true;
  button.textContent="PREPARING...";
  try{
    const response=await fetch("/api/create-session",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({first_winner:username,key:key})
    });
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||"Unable to prepare giveaway.");
    presentationTab.location.href="/presentation/"+data.draw_id;
    showMessage("Presentation screen opened successfully.","success");
  }catch(error){
    presentationTab.close();
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#090a13;--panel:rgba(17,19,35,.88);--purple:#9874ff;--purple-light:#c4aaff;--gold:#f2c879;--muted:#a2a3b8;--white:#fff;--border:rgba(255,255,255,.10)}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;overflow-x:hidden;color:var(--white);font-family:'DM Sans',sans-serif;background-color:var(--bg);background-image:linear-gradient(180deg,rgba(7,8,17,.48),rgba(7,8,17,.92) 75%),linear-gradient(90deg,rgba(7,8,17,.5),rgba(7,8,17,.15),rgba(7,8,17,.5)),url('https://images.unsplash.com/photo-1519608487953-e999c86e7455?auto=format&fit=crop&w=2200&q=85');background-size:cover;background-position:center;background-attachment:fixed}
body:before{content:"";position:fixed;width:650px;height:650px;left:50%;top:-350px;transform:translateX(-50%);background:radial-gradient(circle,rgba(133,91,255,.22),transparent 70%);pointer-events:none;z-index:-1}
header{min-height:86px;padding:0 6%;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.08);background:rgba(8,9,19,.48);backdrop-filter:blur(18px)}
.logo{font-family:'Outfit',sans-serif;font-size:23px;font-weight:900;letter-spacing:1.5px}
.logo span{color:var(--purple-light)}
.header-right{display:flex;align-items:center;gap:10px;color:#c6c5d5;font-size:12px;letter-spacing:1.2px;font-weight:700}
.live-dot{width:8px;height:8px;border-radius:50%;background:#6ce4b2;box-shadow:0 0 12px #6ce4b2}
.main{width:min(1120px,94%);margin:0 auto;padding:76px 0 55px;text-align:center}
.eyebrow{display:inline-flex;align-items:center;gap:9px;color:var(--purple-light);font-size:11px;font-weight:800;letter-spacing:3px;text-transform:uppercase;margin-bottom:22px}
.eyebrow:before,.eyebrow:after{content:"";width:25px;height:1px;background:var(--purple);opacity:.7}
h1{font-family:'Outfit',sans-serif;font-size:clamp(42px,7vw,76px);font-weight:800;letter-spacing:-2.5px;line-height:1.05;margin:0}
h1 span{background:linear-gradient(100deg,#fff 5%,#c5aaff 55%,#9874ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.intro{color:#b4b4c7;font-size:15px;line-height:1.7;max-width:520px;margin:20px auto 43px}
.panel{max-width:660px;margin:0 auto 28px;padding:32px;text-align:left;background:var(--panel);border:1px solid rgba(175,145,255,.22);border-radius:22px;box-shadow:0 25px 90px rgba(0,0,0,.42);backdrop-filter:blur(22px)}
.panel-heading{display:flex;align-items:center;gap:14px;margin-bottom:9px}
.panel-icon{width:43px;height:43px;flex-shrink:0;display:grid;place-items:center;border-radius:13px;background:rgba(152,116,255,.16);color:#c4aaff;font-size:21px}
.panel h2{font-family:'Outfit',sans-serif;font-size:21px;margin:0;font-weight:700}
.panel-description{color:var(--muted);font-size:13px;line-height:1.6;margin:0 0 24px}
label{display:block;color:#deddeb;font-size:12px;font-weight:700;margin:19px 0 9px;letter-spacing:.3px}
input,select{width:100%;height:51px;padding:0 15px;border-radius:10px;border:1px solid rgba(255,255,255,.13);background:rgba(7,8,18,.72);color:#fff;font-family:inherit;font-size:14px;outline:none;transition:border .2s,box-shadow .2s}
input::placeholder{color:#77788d}
input:focus,select:focus{border-color:var(--purple);box-shadow:0 0 0 3px rgba(152,116,255,.12)}
select option{background:#171729;color:white}
button{font-family:inherit;cursor:pointer;border:0;transition:all .2s ease}
.primary{width:100%;min-height:54px;margin-top:25px;border-radius:11px;color:#fff;font-size:12px;font-weight:800;letter-spacing:1.7px;background:linear-gradient(110deg,#7852d8,#a27aff);box-shadow:0 8px 30px rgba(125,83,221,.25)}
.primary:hover{transform:translateY(-2px);box-shadow:0 12px 35px rgba(125,83,221,.4)}
button:disabled{opacity:.55;cursor:wait;transform:none!important}
.message{display:none;margin-top:16px;padding:13px 15px;border-radius:9px;font-size:13px;line-height:1.5}
.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#174235;color:#a7f0d2}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:24px}
.stat{padding:21px 10px;text-align:center;background:rgba(8,9,19,.58);border:1px solid var(--border);border-radius:13px}
.stat strong{display:block;font-family:'Outfit',sans-serif;font-size:31px;color:var(--purple-light);margin-bottom:7px}
.stat span{display:block;font-size:10px;color:#a5a4b9;font-weight:700;letter-spacing:1px}
.game-title{font-family:'Outfit',sans-serif;font-size:clamp(22px,4vw,34px);font-weight:800;margin:0 auto 28px}
.winners{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.card{position:relative;overflow:hidden;min-height:265px;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:25px 18px;border-radius:19px;background:linear-gradient(145deg,rgba(32,29,57,.96),rgba(13,15,29,.96));border:1px solid rgba(168,135,255,.27);box-shadow:0 20px 55px rgba(0,0,0,.3)}
.card:before{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 20%,rgba(255,255,255,.08) 50%,transparent 80%);transform:translateX(-120%)}
.card.revealing:before{animation:shine 1s linear infinite}
@keyframes shine{to{transform:translateX(120%)}}
.card-label{position:relative;font-size:10px;letter-spacing:3px;color:var(--purple-light);font-weight:800;margin-bottom:16px}
.avatar-wrap{position:relative;width:86px;height:86px;margin-bottom:14px;border-radius:50%;padding:3px;background:linear-gradient(135deg,#b58cff,#f2c879);box-shadow:0 0 25px rgba(174,141,255,.22)}
.avatar{display:flex;width:100%;height:100%;align-items:center;justify-content:center;border-radius:50%;overflow:hidden;background:#28243e;color:#e4d6ff;font-family:'Outfit',sans-serif;font-size:27px;font-weight:800}
.avatar img{width:100%;height:100%;object-fit:cover;display:none}
.username{position:relative;font-family:'Outfit',sans-serif;font-size:clamp(21px,3.5vw,35px);font-weight:800;overflow-wrap:anywhere;min-height:43px;color:#fff;text-shadow:0 0 30px rgba(174,141,255,.35)}
.username.waiting{color:#8d8ba3}
.card-caption{position:relative;font-size:9px;letter-spacing:2px;color:#85849c;margin-top:12px}
.card.revealing{animation:pulse 1s ease-in-out infinite alternate;border-color:#bd9aff}
@keyframes pulse{from{box-shadow:0 15px 45px rgba(0,0,0,.4),0 0 5px rgba(163,107,224,.3)}to{box-shadow:0 15px 55px rgba(0,0,0,.4),0 0 30px rgba(163,107,224,.5)}}
.card.revealed{border-color:rgba(242,200,121,.7);background:linear-gradient(145deg,rgba(49,39,57,.97),rgba(19,19,31,.98));box-shadow:0 15px 60px rgba(0,0,0,.4),0 0 35px rgba(242,200,121,.13)}
.card.revealed .card-label{color:var(--gold)}
.card.revealed .username{color:#ffe2a9}
.card.revealed .avatar-wrap{background:linear-gradient(135deg,#ffe2a5,#e4a94e);box-shadow:0 0 28px rgba(242,200,121,.25)}
.draw-area{margin-top:32px}
.draw-button{min-width:250px;min-height:57px;padding:0 35px;border-radius:11px;color:#21182a;background:linear-gradient(110deg,#e8bd70,#ffe2a5);font-size:12px;font-weight:900;letter-spacing:1.5px;box-shadow:0 8px 30px rgba(226,183,105,.18)}
.draw-button:hover{transform:translateY(-2px);box-shadow:0 12px 35px rgba(226,183,105,.32)}
.status{min-height:25px;margin:19px auto 0;color:#b8b4ca;font-size:13px}
.verification{max-width:550px;margin:32px auto 0;padding:27px;background:rgba(20,21,37,.94);border:1px solid rgba(242,200,121,.35);border-radius:17px;box-shadow:0 15px 50px rgba(0,0,0,.25)}
.verification .card-label{margin-bottom:12px;color:var(--gold)}
.verification strong{display:block;font-family:'Outfit',sans-serif;font-size:30px;letter-spacing:5px;color:var(--gold);margin:12px 0}
.verification a{color:#c5aaff;font-size:13px;text-decoration:none}
.verification a:hover{text-decoration:underline}
.footer{padding:30px 15px 35px;text-align:center;color:#77758c;font-size:10px;letter-spacing:2px;border-top:1px solid rgba(255,255,255,.06)}
.hidden{display:none!important}
.confetti{position:fixed;top:-20px;width:9px;height:15px;z-index:10;pointer-events:none;animation:fall linear forwards}
@keyframes fall{to{transform:translateY(110vh) rotate(900deg);opacity:.1}}
@media(max-width:700px){
 header{height:72px;padding:0 5%}.logo{font-size:19px}.header-right{font-size:10px}
 .main{padding:55px 0 35px}h1{letter-spacing:-1.5px}.intro{font-size:14px;margin-bottom:30px}
 .panel{padding:22px 18px;border-radius:17px}.winners{grid-template-columns:1fr}.card{min-height:245px}
 .stats{gap:7px}.stat{padding:16px 5px}.stat strong{font-size:25px}.stat span{font-size:8px;letter-spacing:.5px}
 .verification{padding:22px 14px}
}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
</head>
<body>
<header>
  <div class="logo">GIVEAWAY <span>WINNER</span></div>
  <div class="header-right"><span class="live-dot"></span> LIVE DRAW</div>
</header>

<main class="main">
  <div class="eyebrow">INSTAGRAM GIVEAWAY</div>
  <h1>The entries are in.<br><span>Now, let’s reveal the winners.</span></h1>
  <p class="intro">Load the comments, check the entries, and reveal the winners.</p>

  <section class="panel" id="setupPanel">
    <div class="panel-heading"><div class="panel-icon">✦</div><h2>Giveaway details</h2></div>
    <p class="panel-description">Enter the giveaway information to load all participants.</p>

    <label for="giveawayName">GIVEAWAY NAME</label>
    <input id="giveawayName" placeholder="e.g. Summer Giveaway 2026">

    <label for="postUrl">INSTAGRAM POST LINK</label>
    <input id="postUrl" type="url" placeholder="https://www.instagram.com/p/...">

    <label for="winnerCount">NUMBER OF WINNERS</label>
    <select id="winnerCount">
      <option value="1">1 Winner</option><option value="2" selected>2 Winners</option>
      <option value="3">3 Winners</option><option value="4">4 Winners</option>
      <option value="5">5 Winners</option><option value="6">6 Winners</option>
      <option value="7">7 Winners</option><option value="8">8 Winners</option>
      <option value="9">9 Winners</option><option value="10">10 Winners</option>
    </select>

    <button class="primary" id="loadButton" onclick="loadParticipants()">LOAD PARTICIPANTS</button>
    <div id="loadMessage" class="message"></div>
    <div id="stats" class="hidden">
      <div class="stats">
        <div class="stat"><strong id="commentCount">0</strong><span>TOTAL COMMENTS</span></div>
        <div class="stat"><strong id="participantCount">0</strong><span>UNIQUE USERS</span></div>
        <div class="stat"><strong id="winnerTotal">0</strong><span>WINNERS</span></div>
      </div>
    </div>
  </section>

  <section id="drawPanel" class="hidden">
    <div class="game-title" id="displayGiveawayName"></div>
    <div class="winners" id="winnerCards"></div>
    <div class="draw-area">
      <button class="draw-button" id="drawButton" onclick="revealWinners()">START THE DRAW</button>
      <div class="status" id="status">All participants are ready. Good luck!</div>
    </div>
    <div id="verification" class="verification hidden">
      <div class="card-label">DRAW VERIFICATION</div>
      <div style="color:#aaa5b9;font-size:13px">Result reference</div>
      <strong id="verificationCode"></strong>
      <a href="/verify" target="_blank">Check the results</a>
    </div>
  </section>
</main>

<footer class="footer">GIVEAWAY WINNER &nbsp;·&nbsp; RANDOM DRAW</footer>

<script>
const DRAW_ID = {{ draw_id|tojson }};
let participants = [];
let loaded = false;
let completed = false;

function showMessage(id,text,type){
  const el=document.getElementById(id);
  el.textContent=text;
  el.className="message "+type;
}
function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}

async function loadParticipants(){
  const name=document.getElementById("giveawayName").value.trim();
  const postUrl=document.getElementById("postUrl").value.trim();
  const winnerCount=Number(document.getElementById("winnerCount").value);
  if(!name||!postUrl){showMessage("loadMessage","Please enter the giveaway name and Instagram post link.","error");return;}

  const button=document.getElementById("loadButton");
  button.disabled=true;button.textContent="LOADING PARTICIPANTS...";
  try{
    const response=await fetch("/api/load",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({draw_id:DRAW_ID,giveaway_name:name,post_url:postUrl,winner_count:winnerCount})
    });
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||"Unable to load participants.");

    participants=data.participants;loaded=true;
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
    button.disabled=false;button.textContent="LOAD PARTICIPANTS";
  }
}

function createWinnerCards(count){
  const container=document.getElementById("winnerCards");
  container.innerHTML="";
  for(let i=0;i<count;i++){
    const card=document.createElement("div");
    card.className="card";card.id="card"+i;

    const label=document.createElement("div");
    label.className="card-label";label.textContent="WINNER #"+(i+1);

    const avatarWrap=document.createElement("div");
    avatarWrap.className="avatar-wrap";
    const avatar=document.createElement("div");
    avatar.className="avatar";avatar.id="avatar"+i;
    const initials=document.createElement("span");
    initials.id="initials"+i;initials.textContent="?";
    const img=document.createElement("img");
    img.id="profile"+i;img.alt="Winner profile picture";
    img.referrerPolicy="no-referrer";
    img.onload=()=>{img.style.display="block";initials.style.display="none";};
    img.onerror=()=>{img.style.display="none";initials.style.display="flex";};
    avatar.append(initials,img);avatarWrap.appendChild(avatar);

    const username=document.createElement("div");
    username.className="username waiting";username.id="winner"+i;username.textContent="?";
    const caption=document.createElement("div");
    caption.className="card-caption";caption.textContent="THE WINNER";
    card.append(label,avatarWrap,username,caption);
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

async function loadWinnerProfiles(){
  try{
    const response=await fetch("/api/winner-profiles",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({draw_id:DRAW_ID})
    });
    if(!response.ok)return;
    const data=await response.json();
    (data.profiles||[]).forEach((profile,i)=>{
      const img=document.getElementById("profile"+i);
      const initials=document.getElementById("initials"+i);
      if(profile.url){
        img.src=profile.url;
        initials.textContent=(profile.username||"?").charAt(0).toUpperCase();
      }
    });
  }catch(error){
    // If Instagram does not provide profile images, the initials remain visible.
  }
}

async function revealWinners(){
  if(completed||!loaded)return;
  const button=document.getElementById("drawButton");
  const status=document.getElementById("status");
  const count=Number(document.getElementById("winnerCount").value);
  button.disabled=true;button.textContent="DRAW IN PROGRESS...";
  status.textContent="The draw is underway...";

  const cards=[],names=[];
  for(let i=0;i<count;i++){
    cards.push(document.getElementById("card"+i));
    names.push(document.getElementById("winner"+i));
    cards[i].classList.add("revealing");
    names[i].classList.remove("waiting");
  }

  try{
    const response=await fetch("/api/draw",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({draw_id:DRAW_ID})
    });
    const result=await response.json();
    if(!response.ok)throw new Error(result.error||"The draw could not be completed.");

    const start=Date.now();
    let index=0;
    while(Date.now()-start<6500){
      for(let i=0;i<count;i++){
        const username=participants[(index+i*7)%participants.length];
        names[i].textContent="@"+username;
        document.getElementById("initials"+i).textContent=username.charAt(0).toUpperCase();
      }
      index=(index+1)%participants.length;
      await sleep(90);
    }

    result.winners.forEach((winner,i)=>{
      names[i].textContent="@"+winner;
      document.getElementById("initials"+i).textContent=winner.charAt(0).toUpperCase();
    });
    cards.forEach(card=>{card.classList.remove("revealing");card.classList.add("revealed");});

    status.textContent="Congratulations to our winners!";
    button.textContent="WINNERS ANNOUNCED";
    completed=true;
    document.getElementById("verificationCode").textContent=result.verification_code;
    document.getElementById("verification").classList.remove("hidden");
    confetti();

    // Profile photos are attempted after the winners have been revealed.
    await loadWinnerProfiles();
  }catch(error){
    cards.forEach((card,i)=>{
      card.classList.remove("revealing");
      names[i].textContent="?";names[i].classList.add("waiting");
      document.getElementById("initials"+i).textContent="?";
    });
    status.textContent=error.message;
    button.disabled=false;button.textContent="TRY AGAIN";
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
body{margin:0;min-height:100vh;background:linear-gradient(145deg,#11101d,#211832);color:#fff;font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}
.panel{width:100%;max-width:620px;padding:35px;background:#1b1a2a;border:1px solid #51406b;border-radius:20px;box-shadow:0 20px 70px #0006}
.logo{text-align:center;font-size:25px;font-weight:900;letter-spacing:2px;margin-bottom:10px}
.logo span{color:#b68cff}
.sub{text-align:center;color:#aaa5b9;font-size:13px;margin-bottom:30px}
h1{text-align:center;font-size:25px}
label{display:block;margin:20px 0 8px;color:#d9d6e8;font-size:14px}
input{width:100%;padding:16px;border-radius:9px;border:1px solid #49415c;background:#11101d;color:#fff;font-size:17px}
button{width:100%;margin-top:18px;padding:16px;border:0;border-radius:9px;background:#8755d5;color:white;font-size:14px;font-weight:800;cursor:pointer}
.message{display:none;margin-top:18px;padding:14px;border-radius:9px;line-height:1.5}
.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#1d4539;color:#a7f0d2}
.results{margin-top:25px}
.result-item{padding:14px;margin-top:10px;border-radius:10px;background:#11101d}
.result-item span{display:block;color:#aaa5b9;font-size:11px;margin-bottom:7px}
.result-item strong{font-size:18px;overflow-wrap:anywhere}
</style>
</head>
<body>
<div class="panel">
  <div class="logo">GIVEAWAY <span>WINNER</span></div>
  <div class="sub">Result lookup</div>
  <h1>Verify Giveaway Results</h1>
  <label for="code">Verification Code</label>
  <input id="code" placeholder="GW-XXXXXX" autocomplete="off">
  <button id="verifyButton" onclick="verifyCode()">VERIFY RESULTS</button>
  <div id="message" class="message"></div>
  <div id="results" class="results"></div>
</div>
<script>
function showMessage(text,type){
  const el=document.getElementById("message");
  el.textContent=text;el.className="message "+type;
}
async function verifyCode(){
  const code=document.getElementById("code").value.trim();
  const button=document.getElementById("verifyButton");
  const results=document.getElementById("results");
  results.innerHTML="";
  if(!code){showMessage("Please enter a verification code.","error");return;}
  button.disabled=true;button.textContent="VERIFYING...";
  try{
    const response=await fetch("/api/verify",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({code:code})
    });
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||"Verification failed.");
    const fields=[
      ["Giveaway Name",data.giveaway_name],["Instagram Post",data.post_url],
      ["Date and Time",data.created_at],["Total Comments",data.comment_count],
      ["Unique Participants",data.participant_count],["Number of Winners",data.winner_count]
    ];
    fields.forEach(([label,value])=>{
      const item=document.createElement("div");item.className="result-item";
      const span=document.createElement("span");span.textContent=label;
      const strong=document.createElement("strong");strong.textContent=value;
      item.append(span,strong);results.appendChild(item);
    });
    data.winners.forEach((winner,index)=>{
      const item=document.createElement("div");item.className="result-item";
      const span=document.createElement("span");span.textContent="WINNER #"+(index+1);
      const strong=document.createElement("strong");strong.textContent="@"+winner;
      item.append(span,strong);results.appendChild(item);
    });
    showMessage("Verification successful. These are the recorded results.","success");
  }catch(error){showMessage(error.message,"error");}
  finally{button.disabled=false;button.textContent="VERIFY RESULTS";}
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
    match = re.search(r"instagram\.com/(?:p|reel|tv)/([^/?#]+)", url)
    if not match:
        raise Exception("Invalid Instagram post URL.")
    return match.group(1)


def normalize_username(username):
    return str(username or "").strip().lstrip("@").lower()


def check_key(data):
    supplied = str(data.get("key", ""))
    return bool(EXPORT_KEY and hmac.compare_digest(supplied, EXPORT_KEY))


def fetch_participants(post_url):
    shortcode = extract_shortcode(post_url)

    profile = api_get(IG_USER_ID, {"fields": "id,username"})
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
            "Post not found on Instagram account " + profile.get("username", "")
        )

    comments = get_all_pages(
        f"{target['id']}/comments",
        {"fields": "id,text,timestamp,username", "limit": 100}
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
            f"{missing} comments did not include a username. The draw cannot continue."
        )

    return len(comments), usernames


def fetch_profile_picture(username):
    """
    Instagram Graph API Business Discovery can return profile_picture_url
    for eligible public professional accounts. It will not work for every
    personal/private account or if the app lacks the required access.
    """
    username = normalize_username(username)
    if not re.fullmatch(r"[a-zA-Z0-9._]{1,30}", username):
        return None

    try:
        fields = (
            f"business_discovery.username({username})"
            "{username,profile_picture_url}"
        )
        data = api_get(IG_USER_ID, {"fields": fields})
        discovered = data.get("business_discovery", {})
        return discovered.get("profile_picture_url")
    except Exception:
        # Keep the draw working even if Instagram does not expose this image.
        return None


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
    return render_template_string(PRESENTATION_PAGE, draw_id=draw_id)


@app.route("/verify")
def verify_page():
    return render_template_string(VERIFY_PAGE)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "application": "Giveaway Winner"})


@app.route("/api/create-session", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}
    if not check_key(data):
        return jsonify({"error": "Invalid Export Key."}), 403

    first_winner = normalize_username(data.get("first_winner", ""))
    if not first_winner:
        return jsonify({"error": "First winner username is required."}), 400

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
    return jsonify({"status": "ok", "draw_id": draw_id})


@app.route("/api/load", methods=["POST"])
def load_comments():
    data = request.get_json(silent=True) or {}
    draw_id = data.get("draw_id", "")
    session = DRAW_SESSIONS.get(draw_id)

    if not session:
        return jsonify({"error": "Presentation session not found. Please start again."}), 404
    if session["winners"] is not None:
        return jsonify({"error": "This giveaway has already been completed."}), 400

    giveaway_name = str(data.get("giveaway_name", "")).strip()
    post_url = str(data.get("post_url", "")).strip()
    try:
        winner_count = int(data.get("winner_count", 0))
    except (TypeError, ValueError):
        winner_count = 0

    if not giveaway_name or not post_url:
        return jsonify({"error": "Giveaway name and Instagram URL are required."}), 400
    if winner_count < 1 or winner_count > 10:
        return jsonify({"error": "Choose between 1 and 10 winners."}), 400

    try:
        comment_count, usernames = fetch_participants(post_url)
        first_winner = session["first_winner"]

        if first_winner not in usernames:
            return jsonify({
                "error": "The selected first winner was not found among the participants. Please check the username."
            }), 400
        if winner_count > len(usernames):
            return jsonify({"error": "There are not enough unique participants."}), 400

        eligible = [
            username for normalized, username in usernames.items()
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
        return jsonify({"error": "Draw not found. Please load the post again."}), 404
    if not session["participants"]:
        return jsonify({"error": "Participants have not been loaded."}), 400

    if session["winners"] is None:
        additional_count = session["winner_count"] - 1
        additional_winners = secrets.SystemRandom().sample(
            session["eligible"], additional_count
        )
        first_winner_display = next(
            username for username in session["participants"]
            if normalize_username(username) == session["first_winner"]
        )
        session["winners"] = [first_winner_display] + additional_winners
        session["verification_code"] = generate_verification_code()
        session["created_at"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    return jsonify({
        "status": "ok",
        "winners": session["winners"],
        "verification_code": session["verification_code"]
    })


@app.route("/api/winner-profiles", methods=["POST"])
def winner_profiles():
    data = request.get_json(silent=True) or {}
    draw_id = data.get("draw_id", "")
    session = DRAW_SESSIONS.get(draw_id)

    if not session or not session.get("winners"):
        return jsonify({"error": "Winners have not been drawn."}), 404

    profiles = []
    for username in session["winners"]:
        profiles.append({
            "username": username,
            "url": fetch_profile_picture(username)
        })

    return jsonify({"status": "ok", "profiles": profiles})


@app.route("/api/verify", methods=["POST"])
def verify_results():
    data = request.get_json(silent=True) or {}
    supplied_code = str(data.get("code", "")).strip().upper()
    if not supplied_code:
        return jsonify({"error": "Please enter a verification code."}), 400

    for session in DRAW_SESSIONS.values():
        saved_code = session.get("verification_code")
        if saved_code and hmac.compare_digest(supplied_code, saved_code):
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
