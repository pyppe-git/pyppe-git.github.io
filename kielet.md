<!doctype html>
<html lang="fi">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Kielen opiskelu</title>
<style>
body{
  font-family:Arial,Helvetica,sans-serif;
  margin:20px;
  background:#071126;
  color:#eaf8e6
}
.container{
  max-width:1000px;
  margin:0 auto;
  background:#76a37a;
  padding:16px;
  border-radius:8px
}
.controls{
  display:flex;
  gap:8px;
  align-items:center;
  flex-wrap:wrap
}
button,input,select{
  padding:8px;
  border-radius:6px;
  border:1px solid rgba(24, 127, 175, 0.788);
  background:transparent;
  color:#4957d4
}
.primary{
  background:#042023;
  color:#06b6d4;
  border:none
}
.board{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
  margin-top:12px
}
.col{
  background:rgba(255,255,0,0.02);
  padding:12px;
  border-radius:8px
}
.list{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:8px
}
.item{
  background:#071126;
  padding:8px;
  border-radius:6px;
  cursor:pointer
}
.item.selected{
  outline:2px solid #06b6d4
}
.matched{
  background:#11d111
}
.big{
  font-size:18px;
  padding:10px
}
.footer{
  display:flex;
  justify-content:space-between;
  margin-top:12px;
  color:#eaf8e6
}
@media(max-width:800px){
  .board{grid-template-columns:1fr}
  .list{grid-template-columns:1fr}
}
.hidden{
  display:none !important;
}
</style>
</head>
<body>

<div class="container">
  <h2>Sanojen opiskelu</h2>

  <h3>Syötä sanat (JSON-muodossa)</h3>
  <textarea id="jsonInput" rows="6" style="width:100%;">
[
  ["la rentrée", "lukukausi"],
  ["un jingle", "tunnus"],
  ["clarifier", "selkeyttää"],
  ["un auditeur", "kuuntelija"],
  ["une auditrice", "kuuntelija"],
  ["abriter", "suojata"],
  ["une tempête", "myrsky"],
  ["une inondation", "tulva"],
  ["en particulier", "erityisesti"],
  ["à l'aise", "luonteva"],
  ["un fauteuil", "nojatuoli"],
  ["se poser des questions", "epäillä"],
  ["extrême", "äärimmäinen"],
  ["se rendre compte", "tajuta"],
  ["un dicton", "sanonta"],
  ["un plongeur", "sukeltaja"],
  ["se détacher de", "irtautua"],
  ["une priorité", "etusija"],
  ["s'immerger", "uppoutua"],
  ["entourer", "ympäröidä"],
  ["une habitude", "tottumus"],
  ["un roman", "romaani"],
  ["se décourager", "lannistua"],
  ["une échéance", "määräaika"],
  ["laisser tomber", "hylätä"],
  ["un bénéfice", "hyöty"],
  ["pertinent", "oleellinen"],
  ["audible", "kuultava"],
  ["captivant", "kiehtova"],
  ["une exigence", "vaatimus"],
  ["contraignant", "sitova"],
  ["se détendre", "rentoutua"],
  ["viser", "tavoitella"],
  ["s'entraîner", "harjoitella"],
  ["un gourou", "guru"],
  ["un raccourci", "oikotie"],
  ["préalable", "ennalta"],
  ["consacrer", "omistaa"],
  ["se dépasser", "ylittää"],
  ["convaincre", "vakuuttaa"],
  ["abordable", "edullinen"],
  ["une méfiance", "epäluulo"],
  ["une transcription", "transkriptio"],
  ["s'inscrire", "rekisteröityä"],
  ["gratuit", "ilmainen"],
  ["constater", "havaita"],
  ["expliquer simplement", "selittää"],
  ["l'actualité", "ajankohta"],
  ["progresser", "edistyä"],
  ["atteindre", "saavuttaa"],
  ["un défi", "haaste"]
]
  </textarea>
  <button id="loadJSON" class="primary">Lataa sanat</button>
  <button id="sync">Sync to GitHub</button>
  <button id="loadFromGitHub">Load from GitHub</button>
  <hr>

  <p>Valitse taso: 1 = yhdistä, 2 = kirjoita suomeksi, 3 = kirjoita ranskaksi</p>

  <div class="controls">
    <label for="level">Taso</label>
    <select id="level">
      <option value="1">1</option>
      <option value="2">2</option>
      <option value="3">3</option>
    </select>

    <label for="page">Sivu</label>
    <select id="pageSelect"></select>

    <button id="shuffle" class="primary">Sekoita</button>
    <button id="reset">Aloita</button>
    <label for="pageSize">Sanat/sivu</label>
    <input id="pageSize" type="number" min="1" value="10" style="width:70px">
    <button id="applyPageSize">Aseta</button>
  </div>

  <main id="mainArea"></main>

  <div class="footer">
    <div>
      Pisteet: <span id="score">0</span>
      Yritykset: <span id="attempts">0</span>
    </div>
    <div>
      Jäljellä: <span id="left">0</span>
    </div>
  </div>
</div>


<script>
let WORDS = [];

let PAGE_SIZE = 10;
let pages=[],pageIndex=0,score=0,attempts=0,currentOrder=[];
const pageSizeInput = document.getElementById("pageSize");
const applyPageSizeBtn = document.getElementById("applyPageSize");

applyPageSizeBtn.addEventListener("click", () => {
  const v = parseInt(pageSizeInput.value, 10);
  if (!isNaN(v) && v > 0) {
    PAGE_SIZE = v;
    buildPages();    // luo uudet sivut
    pageIndex = 0;   // palaa sivun alkuun
    render();
    updateStatus();
  }
});

const main=document.getElementById('mainArea'),
      levelSel=document.getElementById('level'),
      pageSel=document.getElementById('pageSelect'),
      shuffleBtn=document.getElementById('shuffle'),
      resetBtn=document.getElementById('reset'),
      scoreEl=document.getElementById('score'),
      attemptsEl=document.getElementById('attempts'),
      leftEl=document.getElementById('left');

function saveUsedWord(word) {
    const data = JSON.parse(localStorage.getItem("usedWords") || "[]");
    if (!data.includes(word)) {
        data.push(word);
        localStorage.setItem("usedWords", JSON.stringify(data));
    }
}

// SYNC to GITHUB -NAPPI ---
document.getElementById("sync").onclick = () => {
    const username = "pyppe-git";
    const repo = "pyppe-git.github.io";
    const path = "data/used_words.json";

    const content = localStorage.getItem("usedWords") || "[]";
    const encoded = encodeURIComponent(content);

    const url =
      `https://github.com/${username}/${repo}/new/main/?filename=${path}&value=${encoded}`;

    window.open(url, "_blank");
};

document.getElementById("loadFromGitHub").addEventListener("click", async () => {
    const username = "pyppe-git";    
    const repo = "pyppe-git.github.io";            
    const path = "data/used_words1.json";  // esim. sama polku kuin syncissä
    const branch = "main";

    const url =
        `https://raw.githubusercontent.com/${username}/${repo}/${branch}/${path}`;

    try {
        const res = await fetch(url, { cache: "no-store" });

        if (!res.ok) {
            alert("Virhe ladattaessa GitHubista: " + res.status);
            return;
        }

        const json = await res.json();

        if (!Array.isArray(json) || !json.every(x => Array.isArray(x) && x.length === 2)) {
            alert("GitHub JSON ei ole muodossa [[fr,fi],...]");
            return;
        }

        WORDS = json;
        localStorage.setItem("usedWords", JSON.stringify(json)); // synkkaa myös localStorageen
        start();

        alert("Sanat ladattu GitHubista!");
    } catch (e) {
        alert("Virhe: " + e.message);
    }
});

document.getElementById("loadJSON").addEventListener("click", () => {
  const t = document.getElementById("jsonInput").value;
  try {
    const data = JSON.parse(t);
    if (!Array.isArray(data) || !data.every(x => Array.isArray(x) && x.length === 2)) {
      alert("Virhe: JSON tulee olla muodossa [[fr,fi], ...]");
      return;
    }
    WORDS = data;
    start();
  } catch (e) {
    alert("JSON virhe: " + e.message);
  }
});

function shuffle(a){
  const c=a.slice();
  for(let i=c.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));
    [c[i],c[j]]=[c[j],c[i]];
  }
  return c;
}

function buildPages(){
  const idx = WORDS.map((_,i)=>i);
  currentOrder = shuffle(idx);
  pages = [];
  for(let i=0;i<currentOrder.length;i+=PAGE_SIZE)
    pages.push(currentOrder.slice(i,i+PAGE_SIZE));
  populatePages();
}

function populatePages(){
  pageSel.innerHTML='';
  for(let i=0;i<pages.length;i++){
    const o=document.createElement('option');
    o.value=i;
    o.textContent=`Sivu ${i+1} (${pages[i].length})`;
    pageSel.appendChild(o);
  }
  pageSel.value=pageIndex;
}

function start(){
  score=0;
  attempts=0;
  buildPages();
  pageIndex=0;
  render();
  updateStatus();
}

function updateStatus(){
  scoreEl.textContent=score;
  attemptsEl.textContent=attempts;
  leftEl.textContent=(pages[pageIndex]||[]).length;
}


/* =========================
   Render
   ========================= */
function render(){
  main.innerHTML='';
  const lvl = parseInt(levelSel.value,10);
  const indices = pages[pageIndex] || [];

  if(lvl===1){
    renderMatch(indices);
    return;
  }
  if(lvl===2){
    renderTypePage(indices, false);   // FI → FR
    return;
  }
  if(lvl===3){
    renderTypePage(indices, true);    // FR → FI
    return;
  }
}



/* -------------- TASO 1 ---------------- */
function renderMatch(indices){
  const fr = shuffle(indices.map(i=>WORDS[i][0]));
  const fi = shuffle(indices.map(i=>WORDS[i][1]));

  const board=document.createElement('div');
  board.className='board';

  const c1=document.createElement('div');
  const c2=document.createElement('div');
  c1.className='col';
  c2.className='col';
  c1.innerHTML='<h3>FR</h3>';
  c2.innerHTML='<h3>FI</h3>';

  const list1=document.createElement('div');
  const list2=document.createElement('div');
  list1.className='list';
  list2.className='list';

  fr.forEach(t=>{
    const b=document.createElement('button');
    b.className='item';
    b.textContent=t;
    b.dataset.fr=t;
    b.onclick=()=>selectItem(b,'fr');
    list1.appendChild(b);
  });

  fi.forEach(t=>{
    const b=document.createElement('button');
    b.className='item';
    b.textContent=t;
    b.dataset.fi=t;
    b.onclick=()=>selectItem(b,'fi');
    list2.appendChild(b);
  });

  c1.appendChild(list1);
  c2.appendChild(list2);
  board.appendChild(c1);
  board.appendChild(c2);
  main.appendChild(board);

  let sFR=null, sFI=null;

  function selectItem(btn,side){
    if(btn.classList.contains('matched'))return;

    if(side==='fr'){
      if(sFR)sFR.classList.remove('selected');
      sFR=btn;
      btn.classList.add('selected');
    }else{
      if(sFI)sFI.classList.remove('selected');
      sFI=btn;
      btn.classList.add('selected');
    }

    if(sFR&&sFI){
      attempts++;
      attemptsEl.textContent=attempts;
      const ok = indices.some(i=>WORDS[i][0]===sFR.dataset.fr && WORDS[i][1]===sFI.dataset.fi);

      if(ok){
        sFR.classList.add('matched');
        sFI.classList.add('matched');
        score+=10;
        scoreEl.textContent=score;
        sFR.disabled=true;
        sFI.disabled=true;
      }else{
        sFR.classList.add('wrong');
        sFI.classList.add('wrong');
        score=Math.max(0,score-2);
        scoreEl.textContent=score;
        setTimeout(()=>{
          sFR.classList.remove('wrong','selected');
          sFI.classList.remove('wrong','selected');
        },600);
      }

      sFR=null; sFI=null;
      const remaining=document.querySelectorAll('.item:not(.matched)').length/2;
      leftEl.textContent=remaining;
    }
  }
}



/* -------------- TASO 2 ---------------- */
/*
  ✅ Kaikki sanat yhdessä jonossa
  ✅ Jos väärin → lisätään takaisin jonoon
  ✅ Päättyy vasta kun kaikki oikein
*/
function renderTypePage(indices, reverse=false){
  main.innerHTML='';

  const col=document.createElement('div');
  col.className='col';
  col.innerHTML=`<h3>Kirjoita ${reverse ? "suomeksi" : "ranskaksi"}</h3>`;

  // luodaan jono sivun sanoista
  let queue = indices.slice();

  const text=document.createElement('div');
  text.style.fontSize='18px';
  text.style.marginBottom='8px';

  const input=document.createElement('input');
  input.className='big';
  input.placeholder=`Kirjoita ${reverse ? "suomeksi" : "ranskaksi"}...`;

  const btn=document.createElement('button');
  btn.className='primary';
  btn.textContent='Tarkista';

  const fb=document.createElement('div');
  fb.style.marginTop='8px';

  col.appendChild(text);
  col.appendChild(input);
  col.appendChild(btn);
  col.appendChild(fb);
  main.appendChild(col);

  function show(){
    if(queue.length===0){
      text.textContent='Sivu valmis – kaikki oikein!';
      input.disabled=true;
      btn.disabled=true;
      leftEl.textContent=0;
      return;
    }

    const idx = queue[0];
    // reverse=false → FI→FR
    // reverse=true  → FR→FI
    text.textContent = reverse ? WORDS[idx][0] : WORDS[idx][1];
    input.value='';
    input.focus();
    leftEl.textContent = queue.length;
  }

  function check(){
    if(queue.length===0) return;

    const idx = queue.shift();
    const correct = reverse ? WORDS[idx][1] : WORDS[idx][0];
    const user = input.value || '';

    attempts++;
    attemptsEl.textContent=attempts;

    const norm=s=>s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().trim();

    if(norm(user)===norm(correct)){
      fb.textContent='Oikein ✓ ' + correct;
      score+=10;
      scoreEl.textContent=score;
    } else {
      fb.textContent='Väärin ✗ Oikea: ' + correct;
      score=Math.max(0,score-2);
      scoreEl.textContent=score;
      queue.push(idx);
    }

    setTimeout(show,350);
  }

  input.addEventListener('keydown',e=>{if(e.key==='Enter')check()});
  btn.addEventListener('click',check);

  leftEl.textContent = queue.length;
  show();
}


/* ========== UI ========== */
levelSel.addEventListener('change',()=>{ render(); });
pageSel.addEventListener('change',()=>{ pageIndex=parseInt(pageSel.value,10); render(); });
shuffleBtn.addEventListener('click',()=>{ start(); });
resetBtn.addEventListener('click',start);
</script>
</body>
</html>
