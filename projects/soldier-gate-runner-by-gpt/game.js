(() => {
  "use strict";

  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");
  const $ = (id) => document.getElementById(id);
  const ui = {
    soldiers: $("soldierCount"), enemy: $("enemyCount"), progress: $("progressCount"),
    fill: $("progressFill"), status: $("statusPill"), message: $("gameMessage"),
    start: $("startOverlay"), end: $("endOverlay"), startButton: $("startButton"),
    replay: $("playAgainButton"), reset: $("resetButton"), fullscreen: $("fullscreenButton"),
    frame: $("gameFrame"), endKicker: $("endKicker"), endTitle: $("endTitle"),
    endCopy: $("endCopy"), endCount: $("endSoldierCount")
  };

  const W = 960, H = 560, PLAYER_Y = 424, MAX_SOLDIERS = 1_000_000_000;
  const testMode = new URLSearchParams(location.search).get("testMode") === "1";
  const testBossCounterattack = testMode && new URLSearchParams(location.search).get("testBossCounterattack") === "1";
  const testShootableTarget = testMode && new URLSearchParams(location.search).get("testShootableTarget") === "1";
  const speed = testMode ? 520 : 136;
  const spawnInterval = testMode ? .96 : 2.05;
  const C = { lime:"#ffd34d", cyan:"#1687f4", red:"#ed3947", purple:"#2d9cff" };
  const add = (n, label) => ({ kind:"add", amount:n, label });
  const pct = (n, label) => ({ kind:"pct", amount:n, label });
  const mult = (n, label) => ({ kind:"mult", amount:n, label });
  const gate = (left, right, index) => ({ type:"gate", left, right, index });
  const shootTarget = (effect, index) => ({ type:"target", effect, index, label:"SHOOT TO BOOST" });

  const ROUND = [
    gate(add(8,"+8"), pct(.5,"+50%"), 1),
    gate(mult(2,"×2"), add(12,"+12"), 2),
    gate(pct(.2,"+20%"), add(-4,"−4"), 3),
    { type:"enemy", count:18, lane:.49, label:"SCOUT SQUAD" },
    gate(add(10,"+10"), mult(2,"×2"), 4),
    gate(add(15,"+15"), pct(.5,"+50%"), 5),
    { type:"enemy", count:26, lane:.55, label:"ENEMY UNIT" },
    shootTarget(add(1,"+1"), 6),
    { type:"enemy", count:32, lane:.46, label:"HEAVY UNIT" },
    gate(add(12,"+12"), pct(.4,"+40%"), 7),
    gate(mult(2,"×2"), add(18,"+18"), 8),
    { type:"boss", hp:76, label:"FINAL COMMANDER" }
  ];

  let mode="ready", soldiers=12, resolved=0, nextIndex=0, events=[];
  let spawnClock=0, fireClock=0, attackClock=0, lane=.5, targetLane=.5, offset=0, lastFrame=0;
  let message="Choose your route. The squad is waiting.", bullets=[], particles=[];
  let totalEnemyHits=0, totalBossHits=0, totalTargetHits=0, lastTargetValue=0;
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const rand=(a,b)=>a+Math.random()*(b-a);

  function roadAt(y) {
    const t=clamp((y-66)/(H-66),0,1), width=lerp(190,830,t);
    return {left:(W-width)/2,right:(W+width)/2,width,t};
  }
  function say(text) { message=text; ui.message.textContent=text; }
  function syncHud() {
    ui.soldiers.textContent=String(soldiers);
    ui.progress.textContent=resolved+" / "+ROUND.length;
    ui.fill.style.width=(resolved/ROUND.length*100)+"%";
    ui.status.textContent=mode==="ready"?"READY":mode==="running"?"IN RUN":mode==="won"?"VICTORY":"DEFEAT";
    ui.status.classList.toggle("status-live",mode==="running");
    ui.status.classList.toggle("status-win",mode==="won");
    ui.status.classList.toggle("status-loss",mode==="lost");
    const activeEnemy=events.filter(e=>e.type==="enemy"&&e.count>0).sort((a,b)=>b.y-a.y)[0];
    const activeTarget=events.filter(e=>e.type==="target").sort((a,b)=>b.y-a.y)[0];
    if(mode==="ready") ui.enemy.textContent="GATES AHEAD";
    else if(mode==="won") ui.enemy.textContent="CLEARED";
    else if(mode==="lost") ui.enemy.textContent="SQUAD LOST";
    else if(events.some(e=>e.type==="boss"&&e.engaged)) ui.enemy.textContent="COMMANDER";
    else if(activeEnemy) ui.enemy.textContent=activeEnemy.count+" ENEMIES";
    else if(activeTarget) ui.enemy.textContent="SHOOT "+activeTarget.effect.label;
    else ui.enemy.textContent="GATES AHEAD";
    canvas.dataset.enemyCount=String(activeEnemy?activeEnemy.count:0);
    canvas.dataset.enemyHits=String(totalEnemyHits);
    canvas.dataset.bossHits=String(totalBossHits);
    canvas.dataset.shootTargetHits=String(totalTargetHits);
    canvas.dataset.shootTargetValue=String(activeTarget?activeTarget.effect.amount:lastTargetValue);
  }
  function resetState() {
    mode="ready"; soldiers=12; resolved=0; nextIndex=0; events=[];
    spawnClock=0; fireClock=0; attackClock=0; lane=.5; targetLane=.5; bullets=[]; particles=[];
    totalEnemyHits=0; totalBossHits=0; totalTargetHits=0; lastTargetValue=0; canvas.dataset.projectiles="0"; canvas.dataset.enemyCount="0"; canvas.dataset.enemyHits="0"; canvas.dataset.bossHits="0"; canvas.dataset.shootTargetHits="0"; canvas.dataset.shootTargetValue="0";
    ui.start.hidden=false; ui.end.hidden=true;
    say("Choose your route. The squad is waiting."); syncHud();
  }
  function startRun() {
    mode="running"; soldiers=12; resolved=0; nextIndex=1;
    if(testBossCounterattack){
      events=[{...ROUND[ROUND.length-1],hp:1000,maxHp:1000,id:ROUND.length-1,y:PLAYER_Y-124,engaged:true,resolved:false}];
      nextIndex=ROUND.length;
    }else if(testShootableTarget){
      const source=ROUND.find(e=>e.type==="target");
      events=source?[{...source,effect:{...source.effect},id:source.index,y:74,engaged:false,resolved:false}]:[];
      nextIndex=ROUND.length;
    }else{
      events=[{...ROUND[0],id:0,y:84,engaged:false,resolved:false}];
    }
    spawnClock=0; fireClock=0; attackClock=0; lane=.5; targetLane=.5; bullets=[]; particles=[];
    totalEnemyHits=0; totalBossHits=0; totalTargetHits=0; lastTargetValue=0;
    canvas.dataset.projectiles="0"; canvas.dataset.enemyCount="0"; canvas.dataset.enemyHits="0"; canvas.dataset.bossHits="0"; canvas.dataset.shootTargetHits="0"; canvas.dataset.shootTargetValue="0";
    ui.start.hidden=true; ui.end.hidden=true;
    say(testShootableTarget?"Target test: hit the blue +1 panel to increase its value.":"Run started. Pick the stronger gate."); syncHud();
  }
  function finishRun(result) {
    if(mode!=="running") return;
    mode=result; ui.end.hidden=false;
    if(result==="won") {
      ui.endKicker.textContent="OPERATION COMPLETE";
      ui.endTitle.innerHTML="LINE<br><em>BROKEN.</em>";
      ui.endCopy.textContent="Commander down. Your squad broke through the final line.";
      say("Commander defeated. Field operation complete.");
      burst(W/2,PLAYER_Y-100,C.lime,40);
    } else {
      ui.endKicker.textContent="OPERATION FAILED";
      ui.endTitle.innerHTML="SQUAD<br><em>OVERRUN.</em>";
      ui.endCopy.textContent="The line held. Reset and choose a stronger route next run.";
      say("Squad lost. Reset to try a different route.");
      burst(W/2,PLAYER_Y-35,C.red,28);
    }
    ui.endCount.textContent=String(soldiers); syncHud();
  }
  function spawnNext() {
    if(nextIndex>=ROUND.length||mode!=="running") return;
    const source=ROUND[nextIndex];
    events.push({...source,...(source.effect?{effect:{...source.effect}}:{}),id:nextIndex,y:74,engaged:false,resolved:false});
    nextIndex++;
  }
  function applyEffect(effect) {
    if(effect.kind==="add") soldiers+=effect.amount;
    else if(effect.kind==="pct") soldiers=Math.round(soldiers*(1+effect.amount));
    else if(effect.kind==="mult") soldiers*=effect.amount;
    soldiers=clamp(Math.round(soldiers),1,MAX_SOLDIERS);
  }
  function resolveGate(e) {
    const effect=lane>=.5?e.right:e.left, before=soldiers;
    applyEffect(effect); resolved++;
    const delta=soldiers-before;
    say("Gate "+e.index+": "+effect.label+"  ·  "+(delta>=0?"+":"")+delta+" units");
    const road=roadAt(PLAYER_Y); burst(road.left+road.width*lane,PLAYER_Y-14,delta>=0?C.lime:C.red,13);
  }
  function resolveShootTarget(e) {
    const before=soldiers;
    const appliedLabel=e.effect.label;
    applyEffect(e.effect);
    resolved++;
    lastTargetValue=e.effect.amount;
    e.resolved=true;
    say("Target "+e.index+": "+appliedLabel+" applied after "+(e.hits||0)+" hits.");
    const road=roadAt(PLAYER_Y);burst(road.left+road.width*.5,PLAYER_Y-14,soldiers>=before?C.lime:C.red,18);
  }
  function resolveEnemy(e) {
    if(soldiers<Math.ceil(e.count*.6)) {
      soldiers=Math.max(0,soldiers-Math.ceil(e.count*.5)); finishRun("lost"); return;
    }
    const losses=Math.max(2,Math.ceil(e.count*.16));
    soldiers=Math.max(1,soldiers-losses); resolved++;
    say(e.label+" cleared  ·  "+losses+" units lost");
    const road=roadAt(e.y); burst(road.left+road.width*e.lane,e.y,C.red,17);
  }
  function burst(x,y,color,count) {
    for(let i=0;i<count;i++) {
      const angle=Math.random()*Math.PI*2, v=rand(35,180);
      particles.push({x,y,vx:Math.cos(angle)*v,vy:Math.sin(angle)*v,life:rand(.24,.7),max:.7,r:rand(1,3.1),color});
    }
  }
  function pointerToLane(e) {
    if(mode!=="running") return;
    const rect=canvas.getBoundingClientRect(), x=(e.clientX-rect.left)/rect.width*W, road=roadAt(PLAYER_Y);
    targetLane=clamp((x-road.left)/road.width,.06,.94);
  }
  function roundRect(x,y,w,h,r,fill,stroke) {
    r=Math.min(r,w/2,h/2); ctx.beginPath(); ctx.moveTo(x+r,y);
    ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r);
    ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
    if(fill){ctx.fillStyle=fill;ctx.fill();} if(stroke){ctx.strokeStyle=stroke;ctx.stroke();}
  }
  function drawBackground(dt) {
    // Bright, simple arcade environment: clear sky, distant green terrain, and a light road.
    const sky=ctx.createLinearGradient(0,0,0,H);
    sky.addColorStop(0,"#35a9f8");
    sky.addColorStop(.34,"#8bd6ff");
    sky.addColorStop(.62,"#d9f3ff");
    sky.addColorStop(1,"#93d85c");
    ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);

    const sun=ctx.createRadialGradient(760,82,5,760,82,170);
    sun.addColorStop(0,"rgba(255,255,255,.7)");
    sun.addColorStop(1,"rgba(255,255,255,0)");
    ctx.fillStyle=sun;ctx.fillRect(570,0,390,250);

    // Soft, low-detail clouds keep the figures and gates as the focal point.
    ctx.fillStyle="rgba(255,255,255,.68)";
    [[115,75,34],[145,69,27],[171,79,37],[685,120,25],[709,111,31],[737,122,27]].forEach(([x,y,r])=>{
      ctx.beginPath();ctx.ellipse(x,y,r,r*.38,0,0,Math.PI*2);ctx.fill();
    });

    ctx.fillStyle="#b8e58b";ctx.beginPath();ctx.moveTo(0,188);
    [[85,161],[170,190],[260,151],[350,187],[447,160],[541,194],[638,154],[730,182],[820,157],[W,177]].forEach(p=>ctx.lineTo(p[0],p[1]));
    ctx.lineTo(W,320);ctx.lineTo(0,320);ctx.closePath();ctx.fill();
    ctx.fillStyle="#81ce5a";ctx.beginPath();ctx.moveTo(0,235);
    [[95,215],[190,243],[298,208],[410,240],[520,214],[625,247],[742,211],[855,238],[W,222]].forEach(p=>ctx.lineTo(p[0],p[1]));
    ctx.lineTo(W,H);ctx.lineTo(0,H);ctx.closePath();ctx.fill();

    // A few simple shrubs beside the road, scaled down near the horizon.
    for(let i=0;i<22;i++){
      const x=(i*97+23)%W,y=229+(i*31)%182,r=5+(i*7)%10;
      ctx.fillStyle=i%2?"rgba(46,151,62,.42)":"rgba(228,255,175,.48)";
      ctx.beginPath();ctx.ellipse(x,y,r*1.5,r*.62,0,0,Math.PI*2);ctx.fill();
    }
    offset=(offset+dt*(mode==="running"?speed*.65:22))%70;
    ctx.strokeStyle="rgba(255,255,255,.25)";ctx.lineWidth=1;
    for(let y=250;y<H;y+=70){ctx.beginPath();ctx.moveTo(0,y+offset);ctx.lineTo(W,y+offset);ctx.stroke();}
  }

  function drawRoad() {
    const top=roadAt(66),bottom=roadAt(H);
    const grad=ctx.createLinearGradient(0,66,0,H);
    grad.addColorStop(0,"#f4f6f8");grad.addColorStop(.52,"#dce2e8");grad.addColorStop(1,"#c6cfd9");

    // Bridge shadow then concrete road surface.
    ctx.beginPath();ctx.moveTo(top.left-5,66);ctx.lineTo(top.right+5,66);ctx.lineTo(bottom.right+7,H);ctx.lineTo(bottom.left-7,H);ctx.closePath();
    ctx.fillStyle="rgba(43,75,101,.2)";ctx.fill();
    ctx.beginPath();ctx.moveTo(top.left,66);ctx.lineTo(top.right,66);ctx.lineTo(bottom.right,H);ctx.lineTo(bottom.left,H);ctx.closePath();
    ctx.fillStyle=grad;ctx.fill();

    // Raised pale curbs and blue-grey guard rails, deliberately simple and readable.
    ctx.lineCap="round";
    ctx.strokeStyle="rgba(74,91,109,.55)";ctx.lineWidth=13;
    ctx.beginPath();ctx.moveTo(top.left-1,67);ctx.lineTo(bottom.left-1,H);ctx.stroke();
    ctx.beginPath();ctx.moveTo(top.right+1,67);ctx.lineTo(bottom.right+1,H);ctx.stroke();
    ctx.strokeStyle="#f8fbff";ctx.lineWidth=7;
    ctx.beginPath();ctx.moveTo(top.left,67);ctx.lineTo(bottom.left,H);ctx.stroke();
    ctx.beginPath();ctx.moveTo(top.right,67);ctx.lineTo(bottom.right,H);ctx.stroke();
    ctx.strokeStyle="#388be0";ctx.lineWidth=2.5;
    ctx.beginPath();ctx.moveTo(top.left,67);ctx.lineTo(bottom.left,H);ctx.stroke();
    ctx.beginPath();ctx.moveTo(top.right,67);ctx.lineTo(bottom.right,H);ctx.stroke();
    ctx.lineCap="butt";

    // White perspective lane markings and small moving road dashes.
    for(const f of [.333,.666]) {
      ctx.strokeStyle="rgba(255,255,255,.76)";ctx.lineWidth=2.3;ctx.setLineDash([13,18]);ctx.lineDashOffset=-offset*1.8;
      ctx.beginPath();ctx.moveTo(lerp(top.left,top.right,f),66);ctx.lineTo(lerp(bottom.left,bottom.right,f),H);ctx.stroke();ctx.setLineDash([]);
    }
    ctx.strokeStyle="rgba(255,255,255,.58)";ctx.lineWidth=1.5;
    for(let y=118;y<H;y+=62){
      const r=roadAt(y+offset),w=lerp(3,15,r.t);
      ctx.beginPath();ctx.moveTo(r.left+12,y+offset);ctx.lineTo(r.left+12+w,y+offset);ctx.stroke();
      ctx.beginPath();ctx.moveTo(r.right-12-w,y+offset);ctx.lineTo(r.right-12,y+offset);ctx.stroke();
    }

    // Guard-rail posts create just enough depth without making the background busy.
    for(let y=90;y<H;y+=Math.max(18,20+y*.035)){
      const r=roadAt(y),h=5+r.t*10;
      ctx.fillStyle="#236eb7";
      roundRect(r.left-5-r.t*2,y-h,3+r.t*3,h,1.5,"#236eb7");
      roundRect(r.right+2,y-h,3+r.t*3,h,1.5,"#236eb7");
    }
  }

  function drawTrooper(x,y,s,enemy) {
    // Original toy-soldier silhouettes with a readable direction:
    // blue allies are shown from behind; red enemies face the player.
    const p=enemy?{
      helmet:"#e8323d",helmetHi:"#ff9298",helmetDark:"#a91f2b",
      vest:"#e8414b",vestHi:"#ff7278",pants:"#863743",boots:"#532631",
      shirt:"#f4d8c5",skin:"#f2c5a6",gun:"#3e4c5c",gunHi:"#c7d0d8",
      pack:"#b62836",outline:"#a42632"
    }:{
      helmet:"#1687f5",helmetHi:"#a1ddff",helmetDark:"#0753a5",
      vest:"#1775db",vestHi:"#59b1ff",pants:"#315d9c",boots:"#173e73",
      shirt:"#fff0d7",skin:"#e9b990",gun:"#33475d",gunHi:"#d6e1ea",
      pack:"#0c5caf",outline:"#1557a5"
    };
    const step=Math.sin(lastFrame*.012+x*.19+y*.09);

    ctx.save();ctx.translate(x,y);ctx.scale(s,s);

    // Ground shadow, separated legs, and chunky boots give the figure a clear silhouette.
    ctx.fillStyle="rgba(30,54,78,.24)";
    ctx.beginPath();ctx.ellipse(0,14,10.5,3.4,0,0,Math.PI*2);ctx.fill();
    ctx.lineCap="round";ctx.lineJoin="round";
    ctx.strokeStyle=p.pants;ctx.lineWidth=4.6;
    ctx.beginPath();
    ctx.moveTo(-2.8,1);ctx.lineTo(-3.5+step*1.2,8.5);
    ctx.moveTo(2.8,1);ctx.lineTo(3.5-step*1.2,8.5);
    ctx.stroke();
    roundRect(-7+step*.7,7.2,5.8,6.1,1.8,p.boots,"rgba(14,35,64,.55)");
    roundRect(1.2-step*.7,7.2,5.8,6.1,1.8,p.boots,"rgba(14,35,64,.55)");
    ctx.strokeStyle="rgba(255,255,255,.32)";ctx.lineWidth=.9;
    ctx.beginPath();ctx.moveTo(-5.9+step*.7,8.4);ctx.lineTo(-2.4+step*.7,8.4);ctx.moveTo(2.2-step*.7,8.4);ctx.lineTo(5.5-step*.7,8.4);ctx.stroke();

    // Arms sit outside the torso so the body does not collapse into a single dot.
    ctx.strokeStyle=p.outline;ctx.lineWidth=7;ctx.beginPath();
    if(enemy){
      ctx.moveTo(-4.6,-5.4);ctx.lineTo(-7.5,-1.8);ctx.lineTo(-5.8,1.8);
      ctx.moveTo(4.6,-5.4);ctx.lineTo(7.2,-2.2);ctx.lineTo(6.1,1.5);
    }else{
      ctx.moveTo(-4.7,-5.5);ctx.lineTo(-7.2,-1.6);ctx.lineTo(-5.8,1.2);
      ctx.moveTo(4.5,-5.4);ctx.lineTo(6.7,-7.6);ctx.lineTo(6.2,-10.2);
    }
    ctx.stroke();
    ctx.strokeStyle=p.shirt;ctx.lineWidth=4.7;ctx.beginPath();
    if(enemy){
      ctx.moveTo(-4.6,-5.4);ctx.lineTo(-7.5,-1.8);ctx.lineTo(-5.8,1.8);
      ctx.moveTo(4.6,-5.4);ctx.lineTo(7.2,-2.2);ctx.lineTo(6.1,1.5);
    }else{
      ctx.moveTo(-4.7,-5.5);ctx.lineTo(-7.2,-1.6);ctx.lineTo(-5.8,1.2);
      ctx.moveTo(4.5,-5.4);ctx.lineTo(6.7,-7.6);ctx.lineTo(6.2,-10.2);
    }
    ctx.stroke();
    roundRect(-7.1,-1,3.2,3.8,1.1,p.boots,p.outline);
    roundRect(4.7,enemy?-1.1:-11.5,3.2,3.8,1.1,p.boots,p.outline);

    // Uniform torso and bold team-colored vest.
    const shirt=ctx.createLinearGradient(-6,-9,6,6);
    shirt.addColorStop(0,"#fff9eb");shirt.addColorStop(1,p.shirt);
    roundRect(-6.3,-9.1,12.6,15.2,3.4,shirt,p.outline);
    const armor=ctx.createLinearGradient(-5.3,-8,5.3,5);
    armor.addColorStop(0,p.vestHi);armor.addColorStop(.48,p.vest);armor.addColorStop(1,p.helmetDark);
    roundRect(-5.4,-8.4,10.8,12.8,2.8,armor,p.outline);
    if(enemy){
      // Chest plate, belt and pouches remain distinct on the opposing front-facing unit.
      roundRect(-3.9,-6.2,7.8,4.2,1.5,"#b82a37","rgba(255,255,255,.24)");
      roundRect(-4.3,1,3,3.1,.8,"#9f2531",p.outline);
      roundRect(1.3,1,3,3.1,.8,"#9f2531",p.outline);
    }else{
      // A broad back plate and segmented pack make the forward-facing direction unambiguous.
      roundRect(-4.1,-7.2,8.2,8.8,2.1,p.pack,p.outline);
      roundRect(-3,-6.2,6,2.1,.7,p.vestHi,"rgba(255,255,255,.3)");
      roundRect(-3.1,-2.8,6.2,3.3,1,p.helmetDark,"rgba(255,255,255,.14)");
      ctx.strokeStyle="rgba(207,233,255,.62)";ctx.lineWidth=.85;
      ctx.beginPath();ctx.moveTo(-4.5,-7);ctx.lineTo(-4.5,3);ctx.moveTo(4.5,-7);ctx.lineTo(4.5,3);ctx.stroke();
    }
    roundRect(-4.5,4,9,1.6,.6,"#dce5ef","rgba(30,64,104,.4)");
    roundRect(-1.1,4.2,2.2,1.2,.4,enemy?"#ffd0d0":"#ffdc56");

    if(enemy){
      // Enemy face and visor are visible because this unit faces the incoming squad.
      ctx.fillStyle=p.skin;ctx.beginPath();
      ctx.arc(-4.1,-12.1,1.5,0,Math.PI*2);ctx.arc(4.1,-12.1,1.5,0,Math.PI*2);ctx.fill();
      const face=ctx.createRadialGradient(-1,-14,0,0,-11.7,5.8);
      face.addColorStop(0,"#ffe0bd");face.addColorStop(1,p.skin);
      ctx.fillStyle=face;ctx.beginPath();ctx.ellipse(0,-11.9,4.5,5.1,0,0,Math.PI*2);ctx.fill();
      ctx.fillStyle="#263849";ctx.beginPath();
      ctx.arc(-1.55,-12.1,.55,0,Math.PI*2);ctx.arc(1.55,-12.1,.55,0,Math.PI*2);ctx.fill();
      ctx.strokeStyle="rgba(108,57,47,.72)";ctx.lineWidth=.7;
      ctx.beginPath();ctx.moveTo(-1.1,-9.8);ctx.quadraticCurveTo(0,-9.1,1.1,-9.8);ctx.stroke();
      ctx.fillStyle=p.helmet;ctx.beginPath();ctx.ellipse(0,-15.3,6.1,4.6,0,Math.PI,Math.PI*2);ctx.fill();
      roundRect(-6,-15.6,12,2.1,.8,p.helmetDark,p.outline);
      ctx.strokeStyle=p.helmetHi;ctx.lineWidth=1.1;
      ctx.beginPath();ctx.ellipse(-.2,-15.7,4.2,2.4,-.04,Math.PI*1.04,Math.PI*1.82);ctx.stroke();
      // The barrel points down-screen toward the player.
      ctx.save();ctx.translate(5.5,-2);ctx.rotate(.12);
      roundRect(-1.8,-2,3.7,7,1,p.gun,p.outline);
      roundRect(-1.05,3.5,2.1,9,0.7,p.gunHi,p.gun);
      roundRect(-1.5,11.5,3,2.2,.5,p.gun,p.outline);
      ctx.restore();
    }else{
      // Oversized helmet is seen from behind; no face or eyes are drawn.
      ctx.fillStyle=p.helmet;ctx.beginPath();ctx.ellipse(0,-14.8,6.5,6.5,0,0,Math.PI*2);ctx.fill();
      ctx.strokeStyle=p.outline;ctx.lineWidth=1.1;ctx.beginPath();ctx.ellipse(0,-14.8,6.5,6.5,0,0,Math.PI*2);ctx.stroke();
      roundRect(-6.3,-13,12.6,2.2,.8,p.helmetDark,p.outline);
      ctx.strokeStyle=p.helmetHi;ctx.lineWidth=1.3;
      ctx.beginPath();ctx.ellipse(-.6,-16.2,4.6,3.6,-.1,Math.PI*1.1,Math.PI*1.85);ctx.stroke();
      roundRect(-1,-20.3,2,1.4,.5,p.helmetHi,"rgba(255,255,255,.7)");
      // Rear-facing rifle points forward/up beyond the helmet.
      ctx.save();ctx.translate(6,-7.5);ctx.rotate(.04);
      roundRect(-2.3,-2.2,4.4,7,1,p.gun,p.outline);
      roundRect(-1.3,-12,2.5,11,0.7,p.gunHi,p.gun);
      roundRect(-1.5,-14.5,3,3.1,.8,p.gun,p.outline);
      ctx.strokeStyle="rgba(255,255,255,.5)";ctx.lineWidth=.65;
      ctx.beginPath();ctx.moveTo(-.6,-10);ctx.lineTo(-.6,-4);ctx.stroke();
      if(mode==="running"&&Math.sin(lastFrame*.085+x*1.7+y)>0.6){
        ctx.fillStyle="rgba(255,211,77,.35)";ctx.beginPath();ctx.arc(0,-15.3,4,0,Math.PI*2);ctx.fill();
        ctx.fillStyle="#fff4a5";ctx.beginPath();
        ctx.moveTo(0,-13.2);ctx.lineTo(-2.6,-16.2);ctx.lineTo(0,-20);ctx.lineTo(2.6,-16.2);ctx.closePath();ctx.fill();
      }
      ctx.restore();
    }
    ctx.restore();
  }

  function drawSquad() {
    const road=roadAt(PLAYER_Y),x=road.left+road.width*lane;
    ctx.fillStyle="rgba(28,130,237,.13)";ctx.beginPath();ctx.ellipse(x,PLAYER_Y+17,91,28,0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle="rgba(23,117,219,.2)";ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(x,PLAYER_Y+17,91,28,0,0,Math.PI*2);ctx.stroke();

    // Rows are broad enough to read as a troop formation, not a tiny triangular icon.
    const count=Math.min(soldiers,48),cols=Math.min(12,Math.max(6,Math.ceil(Math.sqrt(Math.min(soldiers,48))*1.65)));
    const spacing=18+Math.min(32,Math.log2(Math.max(1,soldiers/12))*4);
    const rowSpacing=8.5+Math.min(4,Math.log2(Math.max(1,soldiers/12))*.35);
    for(let i=0;i<count;i++){
      const row=Math.floor(i/cols),col=i%cols;
      const inRow=Math.min(cols,count-row*cols),offset=(cols-inRow)/2;
      const sx=x+(col+offset-(cols-1)/2)*spacing+(row%2?2.2:0);
      const sy=PLAYER_Y-25+row*rowSpacing;
      drawTrooper(sx,sy,.98+row*.025,false);
    }

    // A small clean team marker in place of the previous neon-green caption.
    roundRect(x-48,PLAYER_Y+49,96,17,7,"rgba(255,255,255,.94)","#1f7fe1");
    ctx.fillStyle="#1267bd";ctx.font="900 9px ui-sans-serif,system-ui";ctx.textAlign="center";ctx.textBaseline="middle";
    ctx.fillText("YOUR SQUAD",x,PLAYER_Y+57.4);
    ctx.textBaseline="alphabetic";
  }

  function tint(effect) {
    const negative=effect.kind==="pct"?effect.amount<0:effect.amount<0;
    if(negative)return {c:"#df2939",bg:"rgba(235,54,65,.92)",edge:"#a91d2a"};
    return {c:"#1478e4",bg:"rgba(27,126,231,.94)",edge:"#0b4f9f"};
  }

  function drawGatePanel(x,y,w,h,effect,s,caption="SQUAD") {
    const t=tint(effect);ctx.save();
    const side=Math.max(2,4*s);
    const grad=ctx.createLinearGradient(x,y,x+w,y+h);
    if(t.edge==="#a91d2a"){
      grad.addColorStop(0,"#ff6570");grad.addColorStop(.48,t.bg);grad.addColorStop(1,"#bf2634");
    } else {
      grad.addColorStop(0,"#6ac2ff");grad.addColorStop(.48,t.bg);grad.addColorStop(1,"#145cbb");
    }
    ctx.shadowColor="rgba(25,49,76,.2)";ctx.shadowBlur=7*s;
    roundRect(x,y,w,h,5*s,grad,t.edge);ctx.shadowBlur=0;
    // Thick colored uprights and a white cap make each gate legible at a glance.
    roundRect(x+2*s,y-3*s,side,h+6*s,1.2*s,t.edge);
    roundRect(x+w-side-2*s,y-3*s,side,h+6*s,1.2*s,t.edge);
    roundRect(x+2*s,y-3*s,w-4*s,Math.max(3,3*s),1.2*s,"rgba(255,255,255,.88)");
    ctx.strokeStyle="rgba(255,255,255,.56)";ctx.lineWidth=Math.max(.8,1.2*s);
    ctx.beginPath();ctx.moveTo(x+side+2*s,y+3*s);ctx.lineTo(x+side+2*s,y+h-2*s);ctx.stroke();
    ctx.fillStyle="#fff";ctx.textAlign="center";ctx.textBaseline="middle";
    ctx.lineWidth=Math.max(1,2.2*s);ctx.strokeStyle="rgba(18,47,82,.2)";
    ctx.font="900 "+Math.round(25*s)+"px ui-sans-serif,system-ui";
    ctx.strokeText(effect.label,x+w/2,y+h*.52);ctx.fillText(effect.label,x+w/2,y+h*.52);
    ctx.font="900 "+Math.max(6,Math.round(8*s))+"px ui-sans-serif,system-ui";
    ctx.fillStyle="rgba(255,255,255,.91)";ctx.fillText(caption,x+w/2,y-8*s);
    ctx.restore();
  }

  function drawGate(e) {
    const r=roadAt(e.y),s=.42+r.t*.72,h=21+r.t*37,y=e.y-h,gap=5*s,half=r.width/2;
    drawGatePanel(r.left+4,y,half-7,h,e.left,s);drawGatePanel(r.left+half+gap,y,half-7,h,e.right,s);
    ctx.fillStyle="rgba(4,12,20,.7)";ctx.fillRect(r.left+half-2,y-2,4,h+5);
  }
  function shootTargetGeometry(e) {
    const road=roadAt(e.y),s=.42+road.t*.72,h=21+road.t*37,w=road.width*.72;
    return {road,s,h,w,x:road.left+(road.width-w)/2,y:e.y-h};
  }
  function drawShootTarget(e) {
    const g=shootTargetGeometry(e);
    drawGatePanel(g.x,g.y,g.w,g.h,e.effect,g.s,"SHOOT TO BOOST");
    if((e.hitFlash||0)>0){ctx.save();ctx.strokeStyle="rgba(255,255,255,.9)";ctx.lineWidth=2+g.s;ctx.strokeRect(g.x-3,g.y-3,g.w+6,g.h+6);ctx.restore();}
  }
  function drawEnemy(e) {
    const r=roadAt(e.y),x=r.left+r.width*e.lane,s=.58+r.t*.92;
    ctx.fillStyle="rgba(222,48,59,.14)";ctx.beginPath();ctx.ellipse(x,e.y+13,69*s,20*s,0,0,Math.PI*2);ctx.fill();
    const n=Math.min(32,Math.max(1,Math.round(e.count)));
    for(let i=0;i<n;i++){
      const cols=6,row=Math.floor(i/cols),col=i%cols;
      const inRow=Math.min(cols,n-row*cols),rowOffset=(cols-inRow)/2;
      const sx=x+(col+rowOffset-(cols-1)/2)*18*s+(row%2?2.2*s:0);
      const sy=e.y+row*10*s;
      drawTrooper(sx,sy,s*.9,true);
    }
    const label="ENEMY "+e.count;
    ctx.font="900 "+Math.max(8,Math.round(10*s))+"px ui-sans-serif,system-ui";ctx.textAlign="center";
    const labelY=e.y-25*s,w=ctx.measureText(label).width+16,h=Math.max(14,14*s);
    const flashing=(e.hitFlash||0)>0;
    roundRect(x-w/2,labelY-h/2,w,h,5*s,flashing?"#fff1a6":"rgba(255,255,255,.95)",flashing?"#ffb000":"#dc3745");
    ctx.fillStyle=flashing?"#8a3a00":"#bd2634";ctx.textBaseline="middle";ctx.fillText(label,x,labelY);ctx.textBaseline="alphabetic";
  }

  function drawBoss(e) {
    const r=roadAt(e.y),x=r.left+r.width/2,s=1.08+r.t*.16;
    const glow=ctx.createRadialGradient(x,e.y,8,x,e.y,115);
    glow.addColorStop(0,"rgba(239,55,68,.26)");glow.addColorStop(1,"rgba(239,55,68,0)");
    ctx.fillStyle=glow;ctx.fillRect(x-130,e.y-130,260,235);
    ctx.save();ctx.translate(x,e.y);ctx.scale(s,s);
    ctx.fillStyle="rgba(40,53,69,.22)";ctx.beginPath();ctx.ellipse(0,39,42,13,0,0,Math.PI*2);ctx.fill();

    // The commander shares the toy-soldier silhouette, but gains oversized red armor.
    const armor=ctx.createLinearGradient(-34,-23,34,31);
    armor.addColorStop(0,"#ff7c82");armor.addColorStop(.38,"#e4313e");armor.addColorStop(1,"#9d1f2c");
    roundRect(-31,-18,62,51,9,armor,"#8d1b29");
    roundRect(-40,-10,15,31,4,"#c82a38","#8d1b29");
    roundRect(25,-10,15,31,4,"#ff5c66","#8d1b29");
    roundRect(-23,8,46,8,3,"#6d2632","#8d1b29");
    roundRect(-8,-8,16,18,3,"#303e50","#171f2a");
    roundRect(-4,-7,8,9,2,"#ffdf75","#fff1b0");

    ctx.fillStyle="#f1be98";ctx.beginPath();ctx.ellipse(0,-31,22,22,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle="#e52e3b";ctx.beginPath();
    ctx.moveTo(-25,-34);ctx.lineTo(-20,-50);ctx.lineTo(-8,-47);ctx.lineTo(0,-53);ctx.lineTo(10,-47);ctx.lineTo(21,-50);ctx.lineTo(26,-34);ctx.lineTo(20,-22);ctx.lineTo(-20,-22);ctx.closePath();ctx.fill();
    ctx.strokeStyle="#ff9ca1";ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-16,-42);ctx.quadraticCurveTo(0,-50,16,-42);ctx.stroke();
    roundRect(-15,-32,30,8,3,"#28394e","#fda1a5");
    roundRect(-9,-30,18,3,1.3,"#ffdc58","#fff1a9");

    // Big rifle silhouette, still drawn in the same original Canvas style.
    ctx.save();ctx.translate(23,-4);ctx.rotate(-.46);
    roundRect(-1,-4,10,7,2,"#455266","#233143");
    roundRect(6,-3,23,5,1.5,"#5b6e81","#263b52");
    roundRect(25,-2.5,8,4,1,"#2b3d54","#17273b");
    ctx.restore();ctx.restore();

    ctx.textAlign="center";ctx.font="900 11px ui-sans-serif,system-ui";
    const label="FINAL COMMANDER",labelY=e.y-78;
    roundRect(x-73,labelY-10,146,20,7,"rgba(255,255,255,.97)","#e83b47");
    ctx.fillStyle="#bd2635";ctx.textBaseline="middle";ctx.fillText(label,x,labelY);ctx.textBaseline="alphabetic";
    const bw=140,by=e.y-61;
    roundRect(x-bw/2,by,bw,10,4,"rgba(255,255,255,.95)","#a91d2a");
    if(e.hp>0){
      const hpGrad=ctx.createLinearGradient(x-bw/2,by,x+bw/2,by);
      hpGrad.addColorStop(0,"#ff7780");hpGrad.addColorStop(1,"#d91f31");
      roundRect(x-bw/2+2,by+2,(bw-4)*clamp(e.hp/e.maxHp,0,1),6,3,hpGrad);
    }
  }

  function drawEvents() {
    events.forEach(e=>{
      if(e.type==="gate"&&e.y>62&&e.y<H+60)drawGate(e);
      else if(e.type==="target"&&e.y>62&&e.y<H+60)drawShootTarget(e);
      else if(e.type==="enemy"&&e.y>66&&e.y<PLAYER_Y+80)drawEnemy(e);
      else if(e.type==="boss")drawBoss(e);
    });
  }
  function update(dt) {
    for(let i=particles.length-1;i>=0;i--){const p=particles[i];p.x+=p.vx*dt;p.y+=p.vy*dt;p.vx*=Math.max(0,1-dt*1.6);p.vy*=Math.max(0,1-dt*1.6);p.life-=dt;if(p.life<=0)particles.splice(i,1);}
    if(mode!=="running")return;
    spawnClock+=dt;
    if(nextIndex<ROUND.length&&spawnClock>=spawnInterval){spawnClock-=spawnInterval;spawnNext();}
    lane+=(targetLane-lane)*Math.min(1,dt*7.5);
    for(let i=events.length-1;i>=0;i--){
      const e=events[i];
      if(e.type==="boss"&&e.engaged){updateBoss(e,dt);if(mode!=="running")return;continue;}
      if(e.type==="enemy"&&e.engaged){
        if(e.count<=0){resolveEnemy(e);events.splice(i,1);continue;}
        updateEnemyWave(e,dt);
        if(mode!=="running")return;
        if(e.count<=0){resolveEnemy(e);events.splice(i,1);}
        continue;
      }
      e.y+=speed*dt;
      if(e.type==="gate"&&e.y>=PLAYER_Y-24){resolveGate(e);events.splice(i,1);continue;}
      if(e.type==="target"&&e.y>=PLAYER_Y-24){resolveShootTarget(e);events.splice(i,1);continue;}
      if(e.type==="enemy"&&e.y>=PLAYER_Y-180){
        e.engaged=true;e.y=PLAYER_Y-122;e.attackClock=0;e.hitFlash=0;
        say(e.label+" engaged. Squad firing.");
        continue;
      }
      if(e.type==="boss"&&e.y>=PLAYER_Y-124){e.engaged=true;e.y=PLAYER_Y-119;e.maxHp=e.hp;attackClock=0;say("Final commander engaged. Auto-fire on target.");}
    }
    updatePlayerFire(dt);
    updateBullets(dt);
    if(mode==="running"&&nextIndex>=ROUND.length&&events.length===0)finishRun("won");
  }
  function resolveEnemy(e) {
    resolved++;
    say(e.label+" defeated. Enemy squad eliminated.");
    const road=roadAt(e.y);burst(road.left+road.width*e.lane,e.y,C.red,24);
  }
  function updateEnemyWave(e,dt) {
    e.hitFlash=Math.max(0,(e.hitFlash||0)-dt);
    e.attackClock=(e.attackClock||0)+dt;
    const interval=testMode?0.42:1.05;
    if(e.attackClock<interval)return;
    e.attackClock-=interval;
    const losses=Math.min(soldiers,e.count>=28?2:1);
    soldiers=Math.max(0,soldiers-losses);
    const road=roadAt(PLAYER_Y),px=road.left+road.width*lane;
    burst(px,PLAYER_Y-9,C.red,6);
    say(e.label+" returns fire · "+losses+" unit"+(losses===1?"":"s")+" lost");
    if(soldiers<=0)finishRun("lost");
  }
  function updateBoss(e,dt) {
    if(e.hp<=0){resolved++;events=events.filter(item=>item!==e);finishRun("won");return;}
    attackClock+=dt;
    if(attackClock>=(testMode?0.8:1.05)){
      attackClock-=testMode?0.8:1.05;
      const losses=Math.min(soldiers,soldiers<24?2:Math.max(1,Math.round(soldiers*.015)));
      soldiers=Math.max(0,soldiers-losses);
      const pr=roadAt(PLAYER_Y),px=pr.left+pr.width*lane;
      say("Commander counterattack · "+losses+" unit"+(losses===1?"":"s")+" lost");
      burst(px,PLAYER_Y-10,C.red,8);
      if(soldiers<=0){finishRun("lost");return;}
    }
    if(e.hp<=0){resolved++;events=events.filter(item=>item!==e);finishRun("won");}
  }
  function projectileTargetPoint(target) {
    const road=roadAt(target.y);
    if(target.type==="boss") return {x:road.left+road.width/2,y:target.y-27};
    if(target.type==="target") { const g=shootTargetGeometry(target); return {x:g.x+g.w/2,y:g.y+g.h/2}; }
    return {x:road.left+road.width*target.lane,y:target.y};
  }
  function fireVolley(target) {
    const fromRoad=roadAt(PLAYER_Y),fromX=fromRoad.left+fromRoad.width*lane;
    const velocity=testMode?980:760;
    const shotCount=Math.min(32,3+Math.floor(soldiers/18));
    const formationWidth=Math.min(300,18+soldiers*.7);
    const aim=target?projectileTargetPoint(target):null;
    for(let i=0;i<shotCount;i++){
      const ratio=shotCount===1?0:i/(shotCount-1)-.5;
      const spread=ratio*formationWidth;
      const x=clamp(fromX+spread,fromRoad.left+6,fromRoad.right-6),y=PLAYER_Y-42;
      if(aim){
        let shotAim=aim;
        if(target.type==="target"){
          const rx=aim.x-x,ry=aim.y-y;
          const a=speed*speed-velocity*velocity,b=2*ry*speed,c=rx*rx+ry*ry;
          const flightTime=(-b-Math.sqrt(Math.max(0,b*b-4*a*c)))/(2*a);
          shotAim={x:aim.x,y:Math.min(PLAYER_Y-28,aim.y+speed*flightTime)};
        }
        const dx=shotAim.x-x,dy=shotAim.y-y,dist=Math.hypot(dx,dy)||1;
        bullets.push({x,y,vx:dx/dist*velocity,vy:dy/dist*velocity,life:2.4,targetId:target.id,targetX:shotAim.x,targetY:shotAim.y});
      }else{
        bullets.push({x,y,vx:0,vy:-velocity,life:1.5,targetId:null,targetX:x,targetY:-20});
      }
    }
  }
  function updatePlayerFire(dt) {
    if(mode!=="running")return;
    const target=events.filter(e=>(e.type==="boss"&&e.engaged)||(e.type==="enemy"&&e.engaged&&e.count>0)).sort((a,b)=>b.y-a.y)[0]
      ||events.filter(e=>e.type==="target"&&e.y>66&&e.y<PLAYER_Y-24).sort((a,b)=>b.y-a.y)[0]
      ||null;
    fireClock+=dt;
    const interval=testMode?0.18:0.3;
    while(fireClock>=interval){fireClock-=interval;fireVolley(target);}
  }
  function applyProjectileHit(target) {
    if(target.type==="enemy"){
      if(!target.engaged||target.count<=0)return;
      target.count=Math.max(0,target.count-1);
      target.hitFlash=.14;
      totalEnemyHits++;
      canvas.dataset.enemyHits=String(totalEnemyHits);
    }else if(target.type==="boss"){
      if(!target.engaged||target.hp<=0)return;
      target.hp=Math.max(0,target.hp-1);
      totalBossHits++;
      canvas.dataset.bossHits=String(totalBossHits);
    }else if(target.type==="target"){
      if(!events.includes(target)||target.resolved)return;
      if(target.effect.kind==="add")target.effect.amount+=1;
      else if(target.effect.kind==="mult")target.effect.amount+=1;
      else if(target.effect.kind==="pct")target.effect.amount=Math.round((target.effect.amount+.05)*100)/100;
      if(target.effect.kind==="add")target.effect.label=target.effect.amount>0?"+"+target.effect.amount:target.effect.amount<0?"−"+Math.abs(target.effect.amount):"0";
      else if(target.effect.kind==="mult")target.effect.label="×"+target.effect.amount;
      else if(target.effect.kind==="pct")target.effect.label=target.effect.amount>0?"+"+Math.round(target.effect.amount*100)+"%":target.effect.amount<0?"−"+Math.round(Math.abs(target.effect.amount)*100)+"%":"0%";
      target.hits=(target.hits||0)+1;target.hitFlash=.11;totalTargetHits++;
      canvas.dataset.shootTargetHits=String(totalTargetHits);
      canvas.dataset.shootTargetValue=String(target.effect.amount);
    }
  }
  function updateBullets(dt) {
    const velocity=testMode?980:760;
    for(let i=bullets.length-1;i>=0;i--){
      const b=bullets[i];
      b.x+=b.vx*dt;b.y+=b.vy*dt;b.life-=dt;
      if(b.targetId!==null&&b.targetId!==undefined){
        const remaining=Math.hypot(b.targetX-b.x,b.targetY-b.y);
        if(remaining<=velocity*dt+6){
          const target=events.find(e=>e.id===b.targetId);
          if(target)applyProjectileHit(target);
          burst(b.targetX,b.targetY,target&&target.type==="boss"?C.cyan:C.red,4);
          bullets.splice(i,1);
          continue;
        }
      }
      if(b.life<=0||b.y<0||b.x< -30||b.x>W+30)bullets.splice(i,1);
    }
  }
  function drawBullets() {
    canvas.dataset.projectiles=String(bullets.length);
    ctx.save();
    bullets.forEach(b=>{
      ctx.save();ctx.translate(b.x,b.y);ctx.rotate(Math.atan2(b.vy,b.vx));
      ctx.strokeStyle="rgba(255,211,77,.92)";ctx.lineWidth=1.9;ctx.lineCap="round";
      ctx.shadowColor="#ffc83d";ctx.shadowBlur=4;
      ctx.beginPath();ctx.moveTo(-9,0);ctx.lineTo(-2,0);ctx.stroke();ctx.shadowBlur=0;
      ctx.fillStyle="#fff0a3";ctx.beginPath();ctx.ellipse(1,0,2.3,1.15,0,0,Math.PI*2);ctx.fill();
      ctx.restore();
    });
    ctx.restore();
  }
  function drawParticles() {
    particles.forEach(p=>{ctx.globalAlpha=clamp(p.life/p.max,0,1);ctx.fillStyle=p.color;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();});ctx.globalAlpha=1;
  }
  function frame(now) {
    const dt=lastFrame?Math.min((now-lastFrame)/1000,.05):0;lastFrame=now;
    update(dt);drawBackground(dt);drawRoad();drawEvents();drawSquad();drawBullets();drawParticles();syncHud();
    requestAnimationFrame(frame);
  }

  let pointerDown=false;
  canvas.addEventListener("pointerdown",e=>{if(mode!=="running")return;pointerDown=true;pointerToLane(e);if(canvas.setPointerCapture)canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener("pointermove",e=>{if(pointerDown)pointerToLane(e);});
  canvas.addEventListener("pointerup",()=>{pointerDown=false;});
  canvas.addEventListener("pointercancel",()=>{pointerDown=false;});
  window.addEventListener("keydown",e=>{
    if(mode!=="running")return;
    if(e.key==="ArrowLeft"||e.key.toLowerCase()==="a"){e.preventDefault();targetLane=clamp(targetLane-.16,.06,.94);}
    else if(e.key==="ArrowRight"||e.key.toLowerCase()==="d"){e.preventDefault();targetLane=clamp(targetLane+.16,.06,.94);}
  });
  ui.startButton.addEventListener("click",startRun);ui.replay.addEventListener("click",startRun);ui.reset.addEventListener("click",resetState);
  ui.fullscreen.addEventListener("click",async()=>{try{if(!document.fullscreenElement)await ui.frame.requestFullscreen();else await document.exitFullscreen();}catch(_e){say("Fullscreen is not available in this browser.");}});
  document.addEventListener("fullscreenchange",()=>{ui.fullscreen.setAttribute("aria-label",document.fullscreenElement?"Exit fullscreen":"Enter fullscreen");ui.fullscreen.querySelector("span").textContent=document.fullscreenElement?"EXIT FULLSCREEN":"FULLSCREEN";});
  resetState();requestAnimationFrame(frame);
})();
