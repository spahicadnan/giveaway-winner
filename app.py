
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
:root{
 --bg:#090a13;
 --panel:rgba(17,19,35,.88);
 --panel2:rgba(25,27,47,.92);
 --purple:#9874ff;
 --purple-light:#c4aaff;
 --gold:#f2c879;
 --muted:#a2a3b8;
 --white:#fff;
 --border:rgba(255,255,255,.10);
}

*{box-sizing:border-box}

body{
 margin:0;
 min-height:100vh;
 overflow-x:hidden;
 color:var(--white);
 font-family:'DM Sans',sans-serif;
 background-color:var(--bg);
 background-image:
  linear-gradient(180deg,rgba(7,8,17,.48),rgba(7,8,17,.92) 75%),
  linear-gradient(90deg,rgba(7,8,17,.5),rgba(7,8,17,.15),rgba(7,8,17,.5)),
  url('https://images.unsplash.com/photo-1519608487953-e999c86e7455?auto=format&fit=crop&w=2200&q=85');
 background-size:cover;
 background-position:center;
 background-attachment:fixed;
}

body:before{
 content:"";
 position:fixed;
 width:650px;
 height:650px;
 left:50%;
 top:-350px;
 transform:translateX(-50%);
 background:radial-gradient(circle,rgba(133,91,255,.22),transparent 70%);
 pointer-events:none;
 z-index:-1;
}

*{scrollbar-width:thin;scrollbar-color:#51417b transparent}

header{
 height:86px;
 padding:0 6%;
 display:flex;
 align-items:center;
 justify-content:space-between;
 border-bottom:1px solid rgba(255,255,255,.08);
 background:rgba(8,9,19,.48);
 backdrop-filter:blur(18px);
}

.logo{
 font-family:'Outfit',sans-serif;
 font-size:23px;
 font-weight:900;
 letter-spacing:1.5px;
}

.logo span{color:var(--purple-light)}

.header-right{
 display:flex;
 align-items:center;
 gap:10px;
 color:#c6c5d5;
 font-size:12px;
 letter-spacing:1.2px;
 font-weight:700;
}

.live-dot{
 width:8px;
 height:8px;
 border-radius:50%;
 background:#6ce4b2;
 box-shadow:0 0 12px #6ce4b2;
}

.main{
 width:min(1120px,94%);
 margin:0 auto;
 padding:76px 0 55px;
 text-align:center;
}

.eyebrow{
 display:inline-flex;
 align-items:center;
 gap:9px;
 color:var(--purple-light);
 font-size:11px;
 font-weight:800;
 letter-spacing:3px;
 text-transform:uppercase;
 margin-bottom:22px;
}

.eyebrow:before,.eyebrow:after{
 content:"";
 width:25px;
 height:1px;
 background:var(--purple);
 opacity:.7;
}

h1{
 font-family:'Outfit',sans-serif;
 font-size:clamp(42px,7vw,76px);
 font-weight:800;
 letter-spacing:-2.5px;
 line-height:1.05;
 margin:0;
}

h1 span{
 background:linear-gradient(100deg,#fff 5%,#c5aaff 55%,#9874ff);
 -webkit-background-clip:text;
 background-clip:text;
 color:transparent;
}

.intro{
 color:#b4b4c7;
 font-size:15px;
 line-height:1.7;
 max-width:520px;
 margin:20px auto 43px;
}

.panel{
 max-width:660px;
 margin:0 auto 28px;
 padding:32px;
 text-align:left;
 background:var(--panel);
 border:1px solid rgba(175,145,255,.22);
 border-radius:22px;
 box-shadow:0 25px 90px rgba(0,0,0,.42);
 backdrop-filter:blur(22px);
}

.panel-heading{
 display:flex;
 align-items:center;
 gap:14px;
 margin-bottom:9px;
}

.panel-icon{
 width:43px;
 height:43px;
 flex-shrink:0;
 display:grid;
 place-items:center;
 border-radius:13px;
 background:rgba(152,116,255,.16);
 color:#c4aaff;
 font-size:21px;
}

.panel h2{
 font-family:'Outfit',sans-serif;
 font-size:21px;
 margin:0;
 font-weight:700;
}

.panel-description{
 color:var(--muted);
 font-size:13px;
 line-height:1.6;
 margin:0 0 24px;
}

label{
 display:block;
 color:#deddeb;
 font-size:12px;
 font-weight:700;
 margin:19px 0 9px;
 letter-spacing:.3px;
}

input,select{
 width:100%;
 height:51px;
 padding:0 15px;
 border-radius:10px;
 border:1px solid rgba(255,255,255,.13);
 background:rgba(7,8,18,.72);
 color:#fff;
 font-family:inherit;
 font-size:14px;
 outline:none;
 transition:border .2s,box-shadow .2s;
}

input::placeholder{color:#77788d}

input:focus,select:focus{
 border-color:var(--purple);
 box-shadow:0 0 0 3px rgba(152,116,255,.12);
}

select option{background:#171729;color:white}

button{
 font-family:inherit;
 cursor:pointer;
 border:0;
 transition:all .2s ease;
}

.primary{
 width:100%;
 min-height:54px;
 margin-top:25px;
 border-radius:11px;
 color:#fff;
 font-size:12px;
 font-weight:800;
 letter-spacing:1.7px;
 background:linear-gradient(110deg,#7852d8,#a27aff);
 box-shadow:0 8px 30px rgba(125,83,221,.25);
}

.primary:hover{
 transform:translateY(-2px);
 box-shadow:0 12px 35px rgba(125,83,221,.4);
}

button:disabled{
 opacity:.55;
 cursor:wait;
 transform:none!important;
}

.message{
 display:none;
 margin-top:16px;
 padding:13px 15px;
 border-radius:9px;
 font-size:13px;
 line-height:1.5;
}

.error{display:block;background:#49252e;color:#ffb9c3}
.success{display:block;background:#174235;color:#a7f0d2}

.stats{
 display:grid;
 grid-template-columns:repeat(3,1fr);
 gap:12px;
 margin-top:24px;
}

.stat{
 padding:21px 10px;
 text-align:center;
 background:rgba(8,9,19,.58);
 border:1px solid var(--border);
 border-radius:13px;
}

.stat strong{
 display:block;
 font-family:'Outfit',sans-serif;
 font-size:31px;
 color:var(--purple-light);
 margin-bottom:7px;
}

.stat span{
 display:block;
 font-size:10px;
 color:#a5a4b9;
 font-weight:700;
 letter-spacing:1px;
}

.game-title{
 font-family:'Outfit',sans-serif;
 font-size:clamp(22px,4vw,34px);
 font-weight:800;
 margin:0 auto 28px;
}

.winners{
 display:grid;
 grid-template-columns:repeat(2,minmax(0,1fr));
 gap:18px;
}

.card{
 position:relative;
 overflow:hidden;
 min-height:245px;
 display:flex;
 flex-direction:column;
 justify-content:center;
 align-items:center;
 padding:28px 18px;
 border-radius:19px;
 background:linear-gradient(145deg,rgba(32,29,57,.96),rgba(13,15,29,.96));
 border:1px solid rgba(168,135,255,.27);
 box-shadow:0 20px 55px rgba(0,0,0,.3);
}

.card:before{
 content:"";
 position:absolute;
 inset:0;
 background:linear-gradient(110deg,transparent 20%,rgba(255,255,255,.08) 50%,transparent 80%);
 transform:translateX(-120%);
}

.card.revealing:before{animation:shine 1s linear infinite}

@keyframes shine{
 to{transform:translateX(120%)}
}

.card-label{
 position:relative;
 font-size:10px;
 letter-spacing:3px;
 color:var(--purple-light);
 font-weight:800;
 margin-bottom:25px;
}

.username{
 position:relative;
 font-family:'Outfit',sans-serif;
 font-size:clamp(21px,3.5vw,35px);
 font-weight:800;
 overflow-wrap:anywhere;
 min-height:43px;
 color:#fff;
 text-shadow:0 0 30px rgba(174,141,255,.35);
}

.username.waiting{color:#8d8ba3}

.card-caption{
 position:relative;
 font-size:9px;
 letter-spacing:2px;
 color:#85849c;
 margin-top:24px;
}

.card.revealing{
 animation:pulse 1s ease-in-out infinite alternate;
 border-color:#bd9aff;
}

@keyframes pulse{
 from{box-shadow:0 15px 45px rgba(0,0,0,.4),0 0 5px rgba(163,107,224,.3)}
 to{box-shadow:0 15px 55px rgba(0,0,0,.4),0 0 30px rgba(163,107,224,.5)}
}

.card.revealed{
 border-color:rgba(242,200,121,.7);
 background:linear-gradient(145deg,rgba(49,39,57,.97),rgba(19,19,31,.98));
 box-shadow:0 15px 60px rgba(0,0,0,.4),0 0 35px rgba(242,200,121,.13);
}

.card.revealed .card-label{color:var(--gold)}
.card.revealed .username{color:#ffe2a9}

.draw-area{margin-top:32px}

.draw-button{
 min-width:250px;
 min-height:57px;
 padding:0 35px;
 border-radius:11px;
 color:#21182a;
 background:linear-gradient(110deg,#e8bd70,#ffe2a5);
 font-size:12px;
 font-weight:900;
 letter-spacing:1.5px;
 box-shadow:0 8px 30px rgba(226,183,105,.18);
}

.draw-button:hover{
 transform:translateY(-2px);
 box-shadow:0 12px 35px rgba(226,183,105,.32);
}

.status{
 min-height:25px;
 margin:19px auto 0;
 color:#b8b4ca;
 font-size:13px;
}

.verification{
 max-width:550px;
 margin:32px auto 0;
 padding:27px;
 background:rgba(20,21,37,.94);
 border:1px solid rgba(242,200,121,.35);
 border-radius:17px;
 box-shadow:0 15px 50px rgba(0,0,0,.25);
}

.verification .card-label{margin-bottom:12px;color:var(--gold)}

.verification strong{
 display:block;
 font-family:'Outfit',sans-serif;
 font-size:30px;
 letter-spacing:5px;
 color:var(--gold);
 margin:12px 0;
}

.verification a{
 color:#c5aaff;
 font-size:13px;
 text-decoration:none;
}

.verification a:hover{text-decoration:underline}

.footer{
 padding:30px 15px 35px;
 text-align:center;
 color:#77758c;
 font-size:10px;
 letter-spacing:2px;
 border-top:1px solid rgba(255,255,255,.06);
}

.hidden{display:none!important}

.confetti{
 position:fixed;
 top:-20px;
 width:9px;
 height:15px;
 z-index:10;
 pointer-events:none;
 animation:fall linear forwards;
}

@keyframes fall{
 to{transform:translateY(110vh) rotate(900deg);opacity:.1}
}

@media(max-width:700px){
 header{height:72px;padding:0 5%}
 .logo{font-size:19px}
 .header-right{font-size:10px}
 .main{padding:55px 0 35px}
 h1{letter-spacing:-1.5px}
 .intro{font-size:14px;margin-bottom:30px}
 .panel{padding:22px 18px;border-radius:17px}
 .winners{grid-template-columns:1fr}
 .card{min-height:205px}
 .stats{gap:7px}
 .stat{padding:16px 5px}
 .stat strong{font-size:25px}
 .stat span{font-size:8px;letter-spacing:.5px}
 .verification{padding:22px 14px}
}

@media(prefers-reduced-motion:reduce){
 *,*:before,*:after{
  animation-duration:.01ms!important;
  transition-duration:.01ms!important;
 }
}
</style>
</head>

<body>

<header>
 <div class="logo">GIVEAWAY <span>WINNER</span></div>
 <div class="header-right">
  <span class="live-dot"></span>
  LIVE DRAW EXPERIENCE
 </div>
</header>

<main class="main">

 <div class="eyebrow">THE MOMENT IS HERE</div>

 <h1>Let's see <span>who wins.</span></h1>

 <p class="intro">
  One giveaway. Exciting prizes. A moment everyone is waiting for.
 </p>

 <section class="panel" id="setupPanel">

  <div class="panel-heading">
   <div class="panel-icon">✦</div>
   <h2>Giveaway details</h2>
  </div>

  <p class="panel-description">
   Enter the giveaway information to bring all participants into the draw.
  </p>

  <label for="giveawayName">GIVEAWAY NAME</label>
  <input id="giveawayName" placeholder="e.g. Summer Giveaway 2026">

  <label for="postUrl">INSTAGRAM POST LINK</label>
  <input id="postUrl" type="url" placeholder="https://www.instagram.com/p/...">

  <label for="winnerCount">NUMBER OF WINNERS</label>
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
   <button class="draw-button" id="drawButton" onclick="revealWinners()">
    START THE DRAW
   </button>

   <div class="status" id="status">
    All participants are ready. Good luck!
   </div>
  </div>

  <div id="verification" class="verification hidden">
   <div class="card-label">DRAW VERIFICATION</div>
   <div style="color:#aaa5b9;font-size:13px">Your result reference</div>
   <strong id="verificationCode"></strong>
   <a href="/verify" target="_blank">Check the results</a>
  </div>

 </section>

</main>

<footer class="footer">
 GIVEAWAY WINNER &nbsp;·&nbsp; RANDOM DRAW
</footer>

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
  showMessage("loadMessage","Please enter the giveaway name and Instagram post link.","error");
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
  caption.textContent="THE WINNER";

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
 status.textContent="The draw is underway...";

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

  const start=Date.now();
  let index=0;

  while(Date.now()-start<6500){
   for(let i=0;i<count;i++){
    names[i].textContent="@"+participants[(index+i*7)%participants.length];
   }
   index=(index+1)%participants.length;
   await sleep(90);
  }

  result.winners.forEach((winner,i)=>{
   names[i].textContent="@"+winner;
  });

  cards.forEach(card=>{
   card.classList.remove("revealing");
   card.classList.add("revealed");
  });

  status.textContent="Congratulations to our winners!";
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
