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
  ["la rentrée","lukuvuoden / työkauden alku"],
  ["prendre de l'avance","olla etuajassa"],
  ["analyse","analysoida"]
]
  </textarea>
  <button id="loadJSON" class="primary">Lataa sanat</button>
  <hr>

  <p>Valitse taso: 1 = yhdistä, 2 = kirjoita.</p>

  <div class="controls">
    <label for="level">Taso</label>
    <select id="level">
      <option value="1">1</option>
      <option value="2">2</option>
    </select>

    <label for="page">Sivu</label>
    <select id="pageSelect"></select>

    <button id="shuffle" class="primary">Sekoita</button>
    <button id="reset">Aloita</button>
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

const PAGE_SIZE = 10;
let pages=[],pageIndex=0,score=0,attempts=0,currentOrder=[];

const main=document.getElementById('mainArea'),
      levelSel=document.getElementById('level'),
      pageSel=document.getElementById('pageSelect'),
      shuffleBtn=document.getElementById('shuffle'),
      resetBtn=document.getElementById('reset'),
      scoreEl=document.getElementById('score'),
      attemptsEl=document.getElementById('attempts'),
      leftEl=document.getElementById('left');

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
  const lvl=parseInt(levelSel.value,10);

  if(lvl===1){
    pageSel.classList.remove("hidden");
    renderMatch(pages[pageIndex]||[]);
  } else {
    pageSel.classList.add("hidden");
    renderTypeAll();
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
      if(remaining===0) setTimeout(()=>alert('Sivu suoritettu! Pisteet: '+score),300);
    }
  }
}



/* -------------- TASO 2 ---------------- */
/*
  ✅ Kaikki sanat yhdessä jonossa
  ✅ Jos väärin → lisätään takaisin jonoon
  ✅ Päättyy vasta kun kaikki oikein
*/
function renderTypeAll(){
  const col=document.createElement('div');
  col.className='col';
  col.innerHTML='<h3>Kirjoita ranskaksi</h3>';

  let queue = shuffle(WORDS.map((_,i)=>i));  // index-jono

  const text=document.createElement('div');
  text.style.fontSize='18px';
  text.style.marginBottom='8px';

  const input=document.createElement('input');
  input.className='big';
  input.placeholder='Kirjoita ranskaksi...';

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
      text.textContent='Valmis – kaikki oikein!';
      input.disabled=true;
      btn.disabled=true;
      leftEl.textContent=0;
      return;
    }
    const idx = queue[0];
    text.textContent = WORDS[idx][1];
    input.value='';
    input.focus();
    leftEl.textContent = queue.length;
  }

  function check(){
    if(queue.length===0) return;

    const idx = queue.shift(); 
    const correct = WORDS[idx][0];
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
      queue.push(idx);   // ← palautetaan jonon loppuun!
    }

    setTimeout(show,350);
  }

  btn.addEventListener('click',check);
  input.addEventListener('keydown',e=>{if(e.key==='Enter')check()});

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
