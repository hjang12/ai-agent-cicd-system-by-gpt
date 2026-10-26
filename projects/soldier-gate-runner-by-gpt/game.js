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
  const testProjectileRoadBounds = testMode && new URLSearchParams(location.search).get("testProjectileRoadBounds") === "1";
  const testAimedProjectileRoadBounds = testMode && new URLSearchParams(location.search).get("testAimedProjectileRoadBounds") === "1";
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
  let message="Choose your route. The squad is waiting.", bullets=[], particles=[], muzzleFlashes=[];
  let totalEnemyHits=0, totalBossHits=0, totalTargetHits=0, lastTargetValue=0;
  let roadChecks=0, roadViolations=0;
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const rand=(a,b)=>a+Math.random()*(b-a);

  function roadAt(y) {
    const t=clamp((y-66)/(H-66),0,1), width=lerp(190,830,t);
    return {left:(W-width)/2,right:(W+width)/2,width,t};
  }
  function roadXAtLane(y,lanePosition) {
    const road=roadAt(y);
    return road.left+road.width*clamp(lanePosition,.06,.94);
  }
  function squadFormation() {
    const count=Math.min(soldiers,72);
    const cols=Math.min(12,Math.max(1,Math.ceil(Math.sqrt(count)*1.65)));
    const desiredSpacing=18+Math.min(32,Math.log2(Math.max(1,soldiers/12))*4);
    const muzzleRoad=roadAt(PLAYER_Y-47);
    const maxSpacing=cols>1?Math.max(12,(muzzleRoad.width*.76-28)/(cols-1)):desiredSpacing;
    const spacing=Math.min(desiredSpacing,maxSpacing);
    const rowSpacing=12.5+Math.min(3,Math.log2(Math.max(1,soldiers/12))*.3);
    const halfWidth=((Math.min(cols,count)-1)/2)*spacing+24;
    const minCenter=muzzleRoad.left+halfWidth+5;
    const maxCenter=muzzleRoad.right-halfWidth-5;
    const playerRoad=roadAt(PLAYER_Y);
    const desiredCenter=playerRoad.left+playerRoad.width*lane;
    const centerX=minCenter<=maxCenter?clamp(desiredCenter,minCenter,maxCenter):W/2;
    return {count,cols,spacing,rowSpacing,centerX,halfWidth};
  }
  function squadSoldierPosition(formation,index) {
    const row=Math.floor(index/formation.cols),col=index%formation.cols;
    const inRow=Math.min(formation.cols,formation.count-row*formation.cols);
    const rowOffset=(formation.cols-inRow)/2;
    return {
      x:formation.centerX+(col+rowOffset-(formation.cols-1)/2)*formation.spacing+(row%2?2.2:0),
      y:PLAYER_Y-25+row*formation.rowSpacing
    };
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
    canvas.dataset.roadChecks=String(roadChecks);
    canvas.dataset.roadViolations=String(roadViolations);
  }
  function resetState() {
    mode="ready"; soldiers=12; resolved=0; nextIndex=0; events=[];
    spawnClock=0; fireClock=0; attackClock=0; lane=.5; targetLane=.5; bullets=[]; particles=[]; muzzleFlashes=[];
    totalEnemyHits=0; totalBossHits=0; totalTargetHits=0; lastTargetValue=0; roadChecks=0; roadViolations=0;
    canvas.dataset.projectiles="0"; canvas.dataset.enemyCount="0"; canvas.dataset.enemyHits="0"; canvas.dataset.bossHits="0"; canvas.dataset.shootTargetHits="0"; canvas.dataset.shootTargetValue="0"; canvas.dataset.roadChecks="0"; canvas.dataset.roadViolations="0";
    ui.start.hidden=false; ui.end.hidden=true;
    say("Choose your route. The squad is waiting."); syncHud();
  }
  function startRun() {
    mode="running"; soldiers=12; resolved=0; nextIndex=1;
    if(testProjectileRoadBounds||testAimedProjectileRoadBounds){
      soldiers=MAX_SOLDIERS; lane=.06; targetLane=.06;
      if(testAimedProjectileRoadBounds){
        events=[{...ROUND[ROUND.length-1],hp:1000,maxHp:1000,id:ROUND.length-1,y:PLAYER_Y-124,engaged:true,resolved:false}];
      }else{
        events=[{type:"fixture",id:-1,y:200,engaged:false,resolved:false}];
      }
      nextIndex=ROUND.length;
    }else if(testBossCounterattack){
      events=[{...ROUND[ROUND.length-1],hp:1000,maxHp:1000,id:ROUND.length-1,y:PLAYER_Y-124,engaged:true,resolved:false}];
      nextIndex=ROUND.length;
    }else if(testShootableTarget){
      const source=ROUND.find(e=>e.type==="target");
      events=source?[{...source,effect:{...source.effect},id:source.index,y:96,engaged:false,resolved:false}]:[];
      nextIndex=ROUND.length;
    }else{
      events=[{...ROUND[0],id:0,y:96,engaged:false,resolved:false}];
    }
    spawnClock=0; fireClock=0; attackClock=0;
    if(!testProjectileRoadBounds&&!testAimedProjectileRoadBounds){lane=.5;targetLane=.5;}
    bullets=[]; particles=[]; muzzleFlashes=[];
    totalEnemyHits=0; totalBossHits=0; totalTargetHits=0; lastTargetValue=0; roadChecks=0; roadViolations=0;
    canvas.dataset.projectiles="0"; canvas.dataset.enemyCount="0"; canvas.dataset.enemyHits="0"; canvas.dataset.bossHits="0"; canvas.dataset.shootTargetHits="0"; canvas.dataset.shootTargetValue="0"; canvas.dataset.roadChecks="0"; canvas.dataset.roadViolations="0";
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
    events.push({...source,...(source.effect?{effect:{...source.effect}}:{}),id:nextIndex,y:96,engaged:false,resolved:false});
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
    // Reference-inspired clean blue surroundings keep the squad and road as the focal point.
    const sky=ctx.createLinearGradient(0,0,0,H);
    sky.addColorStop(0,"#079ef1");
    sky.addColorStop(.48,"#20b9fa");
    sky.addColorStop(1,"#0789de");
    ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);

    // A soft, restrained horizon glow adds depth without introducing detailed scenery.
    const haze=ctx.createLinearGradient(0,0,0,250);
    haze.addColorStop(0,"rgba(202,245,255,0)");
    haze.addColorStop(.72,"rgba(202,245,255,.14)");
    haze.addColorStop(1,"rgba(202,245,255,0)");
    ctx.fillStyle=haze;ctx.fillRect(0,0,W,250);

    offset=(offset+dt*(mode==="running"?speed*.65:22))%70;
  }

  function drawRoad() {
    const top=roadAt(66),bottom=roadAt(H);
    const grad=ctx.createLinearGradient(0,66,0,H);
    grad.addColorStop(0,"#dce0e3");
    grad.addColorStop(.48,"#d1d6da");
    grad.addColorStop(1,"#c4cbd0");

    // A restrained drop shadow separates the gray road from the blue surroundings.
    ctx.beginPath();ctx.moveTo(top.left-4,66);ctx.lineTo(top.right+4,66);ctx.lineTo(bottom.right+5,H);ctx.lineTo(bottom.left-5,H);ctx.closePath();
    ctx.fillStyle="rgba(28,59,82,.2)";ctx.fill();
    ctx.beginPath();ctx.moveTo(top.left,66);ctx.lineTo(top.right,66);ctx.lineTo(bottom.right,H);ctx.lineTo(bottom.left,H);ctx.closePath();
    ctx.fillStyle=grad;ctx.fill();

    // Broad, subtle transverse sections echo the simple segmented road in the reference.
    ctx.save();
    ctx.beginPath();ctx.moveTo(top.left,66);ctx.lineTo(top.right,66);ctx.lineTo(bottom.right,H);ctx.lineTo(bottom.left,H);ctx.closePath();
    ctx.clip();
    let y=66-(offset%42),band=0;
    while(y<H){
      const t=clamp((y-66)/(H-66),0,1);
      const h=15+t*30;
      const next=Math.min(H,y+h);
      if(band%2===0){
        const r1=roadAt(Math.max(66,y)),r2=roadAt(next);
        ctx.beginPath();ctx.moveTo(r1.left,y);ctx.lineTo(r1.right,y);ctx.lineTo(r2.right,next);ctx.lineTo(r2.left,next);ctx.closePath();
        ctx.fillStyle="rgba(255,255,255,.075)";ctx.fill();
      }else{
        const r1=roadAt(Math.max(66,y)),r2=roadAt(next);
        ctx.beginPath();ctx.moveTo(r1.left,y);ctx.lineTo(r1.right,y);ctx.lineTo(r2.right,next);ctx.lineTo(r2.left,next);ctx.closePath();
        ctx.fillStyle="rgba(63,78,90,.025)";ctx.fill();
      }
      y=next;band++;
    }
    ctx.restore();

    // Thin white road edges replace the bulky guard rails; the blue outside remains visible.
    ctx.lineCap="round";
    ctx.strokeStyle="rgba(57,71,83,.65)";ctx.lineWidth=7;
    ctx.beginPath();ctx.moveTo(top.left,67);ctx.lineTo(bottom.left,H);ctx.stroke();
    ctx.beginPath();ctx.moveTo(top.right,67);ctx.lineTo(bottom.right,H);ctx.stroke();
    ctx.strokeStyle="#f8fbff";ctx.lineWidth=3.5;
    ctx.beginPath();ctx.moveTo(top.left,67);ctx.lineTo(bottom.left,H);ctx.stroke();
    ctx.beginPath();ctx.moveTo(top.right,67);ctx.lineTo(bottom.right,H);ctx.stroke();
    ctx.lineCap="butt";

    // One center divider matches the two-way arithmetic-gate layout.
    ctx.strokeStyle="rgba(255,255,255,.82)";ctx.lineWidth=2.5;ctx.setLineDash([16,17]);ctx.lineDashOffset=-offset*1.8;
    ctx.beginPath();ctx.moveTo(W/2,66);ctx.lineTo(W/2,H);ctx.stroke();ctx.setLineDash([]);

    // Small broken edge marks make the road perspective legible without adding rail hardware.
    ctx.strokeStyle="rgba(255,255,255,.48)";ctx.lineWidth=1.3;
    for(let y=113;y<H;y+=68){
      const r=roadAt(y+offset*.55),w=3+r.t*6;
      ctx.beginPath();ctx.moveTo(r.left+10,y+offset*.55);ctx.lineTo(r.left+10+w,y+offset*.55);ctx.stroke();
      ctx.beginPath();ctx.moveTo(r.right-10-w,y+offset*.55);ctx.lineTo(r.right-10,y+offset*.55);ctx.stroke();
    }
  }

  function drawTrooper(x,y,s,enemy) {
    // Original toy-soldier silhouettes with a readable direction:
    // blue allies are shown from behind; red enemies face the player.
    const p=enemy?{
      helmet:"#e8323d",helmetHi:"#ff9298",helmetDark:"#a91f2b",
      vest:"#d94a51",vestHi:"#ff858a",pants:"#8d3643",boots:"#d52e43",bootOutline:"#8f1f30",glove:"#6d2632",
      shirt:"#f4d8c5",skin:"#f2c5a6",gun:"#3e4c5c",gunHi:"#c7d0d8",
      pack:"#b62836",outline:"#a42632"
    }:{
      helmet:"#1687f5",helmetHi:"#b2e5ff",helmetDark:"#0753a5",
      vest:"#327fb5",vestHi:"#80c6ee",pants:"#315d9c",boots:"#d83b4d",bootOutline:"#8c2635",glove:"#164d85",
      shirt:"#fff0d7",skin:"#e9b990",gun:"#33475d",gunHi:"#d6e1ea",
      pack:"#0c5caf",outline:"#1557a5"
    };
    const step=Math.sin(lastFrame*.012+x*.19+y*.09);

    ctx.save();ctx.translate(x,y);ctx.scale(s,s);

    // Ground shadow, separated legs, and chunky boots give the figure a clear silhouette.
    ctx.fillStyle="rgba(30,54,78,.24)";
    ctx.beginPath();ctx.ellipse(0,14,10.5,3.4,0,0,Math.PI*2);ctx.fill();
    ctx.lineCap="round";ctx.lineJoin="round";
    // Block-shaped trousers and bright boot toes make the lower body readable at small sizes.
    roundRect(-4.5+step*.45,1.3,3.7,8.6,1.15,p.pants,p.outline);
    roundRect(.8-step*.45,1.3,3.7,8.6,1.15,p.pants,p.outline);
    ctx.strokeStyle="rgba(255,255,255,.19)";ctx.lineWidth=.75;
    ctx.beginPath();ctx.moveTo(-2.6+step*.45,2.1);ctx.lineTo(-2.6+step*.45,7.6);ctx.moveTo(2.5-step*.45,2.1);ctx.lineTo(2.5-step*.45,7.6);ctx.stroke();
    roundRect(-7+step*.7,7.3,5.9,5.9,1.8,p.boots,p.bootOutline);
    roundRect(1.2-step*.7,7.3,5.9,5.9,1.8,p.boots,p.bootOutline);
    roundRect(-6.3+step*.7,8,4.2,1.7,.7,"rgba(255,255,255,.3)");
    roundRect(1.9-step*.7,8,4.2,1.7,.7,"rgba(255,255,255,.3)");
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
    // Reset the arm stroke width before small equipment and torso outlines are drawn.
    ctx.lineWidth=1.15;
    roundRect(-7.1,-1,3.2,3.8,1.1,p.glove,p.outline);
    roundRect(4.7,enemy?-1.1:-11.5,3.2,3.8,1.1,p.glove,p.outline);

    // Uniform torso and bold team-colored vest.
    const shirt=ctx.createLinearGradient(-6,-9,6,6);
    shirt.addColorStop(0,"#fff9eb");shirt.addColorStop(1,p.shirt);
    roundRect(-6.3,-9.1,12.6,15.2,3.4,shirt,p.outline);
    const armor=ctx.createLinearGradient(-3.5,-7,3.5,4);
    armor.addColorStop(0,p.vestHi);armor.addColorStop(.48,p.vest);armor.addColorStop(1,p.helmetDark);
    // Keep the vest compact so the light shirt remains a clear part of the soldier silhouette.
    roundRect(-2.8,-6.7,5.6,9.5,2.0,armor,p.outline);
    roundRect(-3.25,-7.3,.4,8.4,.25,p.helmetDark,p.outline);
    roundRect(2.85,-7.3,.4,8.4,.25,p.helmetDark,p.outline);
    if(enemy){
      // A compact chest plate, shoulder guards and pouches preserve the cream shirt silhouette.
      roundRect(-2.5,-5.5,5,3.2,1.1,p.helmetDark,"rgba(255,255,255,.3)");
      roundRect(-3.1,-1,2.1,3.1,.7,"#a92532",p.outline);
      roundRect(1,-1,2.1,3.1,.7,"#a92532",p.outline);
      ctx.strokeStyle="rgba(255,242,221,.58)";ctx.lineWidth=.8;
      ctx.beginPath();ctx.moveTo(-2.4,-4.5);ctx.lineTo(2.4,-4.5);ctx.stroke();
    }else{
      // A compact field pack and side pouches retain the reference's pale shirt / blue gear contrast.
      roundRect(-1.8,-7.1,3.6,8,1.4,p.pack,p.outline);
      roundRect(-1.4,-6.2,2.8,1.7,.6,p.vestHi,"rgba(255,255,255,.35)");
      roundRect(-1.3,-3.5,2.6,2.5,.8,p.helmetDark,"rgba(255,255,255,.16)");
      ctx.strokeStyle="rgba(207,233,255,.72)";ctx.lineWidth=.9;
      roundRect(-5.9,-4.5,1.4,4.4,.8,p.helmetDark,p.outline);
      roundRect(4.5,-4.5,1.4,4.4,.8,p.helmetDark,p.outline);
      roundRect(-5.6,-3.5,.7,1.8,.35,p.vestHi,"rgba(255,255,255,.22)");
      roundRect(4.85,-3.5,.7,1.8,.35,p.vestHi,"rgba(255,255,255,.22)");
      ctx.beginPath();ctx.moveTo(-3.05,-7);ctx.lineTo(-3.05,2);ctx.moveTo(3.05,-7);ctx.lineTo(3.05,2);
      ctx.moveTo(-1.6,-5.5);ctx.lineTo(1.6,-5.5);ctx.stroke();
    }
    roundRect(-4.5,4,9,1.6,.6,"#dce5ef","rgba(30,64,104,.4)");
    roundRect(-1.1,4.2,2.2,1.2,.4,enemy?"#ffd0d0":"#ffdc56");

    if(enemy){
      // Shoulder armor and front pouches break up the torso into readable equipment layers.
      roundRect(-6.3,-8.7,3.1,4.1,1.2,p.helmetDark,p.outline);
      roundRect(3.2,-8.7,3.1,4.1,1.2,p.helmetDark,p.outline);
      roundRect(-3.9,-1.7,2.3,3.2,.8,"#a92532",p.outline);
      roundRect(1.6,-1.7,2.3,3.2,.8,"#a92532",p.outline);
      ctx.strokeStyle="rgba(255,224,224,.48)";ctx.lineWidth=.8;
      ctx.beginPath();ctx.moveTo(-4.1,-4.4);ctx.lineTo(4.1,-4.4);ctx.stroke();
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
      ctx.fillStyle=p.helmet;ctx.beginPath();ctx.ellipse(0,-15.3,6.8,5.1,0,Math.PI,Math.PI*2);ctx.fill();
      roundRect(-6.7,-15.7,13.4,2.2,.8,p.helmetDark,p.outline);
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
      ctx.fillStyle=p.helmet;ctx.beginPath();ctx.ellipse(0,-14.8,7.1,6.8,0,0,Math.PI*2);ctx.fill();
      ctx.strokeStyle=p.outline;ctx.lineWidth=1.1;ctx.beginPath();ctx.ellipse(0,-14.8,7.1,6.8,0,0,Math.PI*2);ctx.stroke();
      roundRect(-6.9,-13,13.8,2.5,.8,p.helmetDark,p.outline);
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
    const formation=squadFormation(),road=roadAt(PLAYER_Y),x=formation.centerX;
    const shadowWidth=Math.min(road.width*.46,formation.halfWidth+24);
    const formationRows=Math.ceil(formation.count/formation.cols);
    const shadowHeight=Math.min(55,28+formation.rowSpacing*Math.max(0,formationRows-1)*.35);
    ctx.fillStyle="rgba(28,130,237,.15)";ctx.beginPath();ctx.ellipse(x,PLAYER_Y+20,shadowWidth,shadowHeight,0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle="rgba(23,117,219,.24)";ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(x,PLAYER_Y+20,shadowWidth,shadowHeight,0,0,Math.PI*2);ctx.stroke();

    // Use the same formation geometry for rendered soldiers and their muzzle positions.
    for(let i=0;i<formation.count;i++){
      const p=squadSoldierPosition(formation,i);
      const row=Math.floor(i/formation.cols);
      drawTrooper(p.x,p.y,.98+row*.025,false);
    }

    // Keep the marker below the formation so larger squads do not cover it.
    const labelY=PLAYER_Y+72;
    roundRect(x-48,labelY,96,17,7,"rgba(255,255,255,.96)","#1f7fe1");
    ctx.fillStyle="#1267bd";ctx.font="900 9px ui-sans-serif,system-ui";ctx.textAlign="center";ctx.textBaseline="middle";
    ctx.fillText("YOUR SQUAD",x,labelY+8.4);
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
      const sy=e.y+row*12*s;
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
    if((e.hitFlash||0)>0){
      ctx.save();ctx.globalAlpha=clamp(e.hitFlash/.14,0,1);ctx.strokeStyle="#fff3ad";ctx.lineWidth=3;
      ctx.beginPath();ctx.ellipse(x,e.y-8,45*s,55*s,0,0,Math.PI*2);ctx.stroke();ctx.restore();
    }

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
    for(let i=muzzleFlashes.length-1;i>=0;i--){muzzleFlashes[i].life-=dt;if(muzzleFlashes[i].life<=0)muzzleFlashes.splice(i,1);}
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
    e.hitFlash=Math.max(0,(e.hitFlash||0)-dt);
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
    const formation=squadFormation();
    const velocity=testMode?980:760;
    const shotCount=Math.min(32,3+Math.floor(soldiers/18),formation.count);
    const aim=target?projectileTargetPoint(target):null;
    for(let i=0;i<shotCount;i++){
      const index=shotCount===1?Math.floor((formation.count-1)/2):Math.round(i*(formation.count-1)/(shotCount-1));
      const soldier=squadSoldierPosition(formation,index);
      const y=soldier.y-22;
      const sourceRoad=roadAt(y);
      const x=clamp(soldier.x+6,sourceRoad.left+10,sourceRoad.right-10);
      muzzleFlashes.push({x:x+1,y:y-1,life:.075,max:.075});
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
        // Keep unguided forward fire inside the perspective road corridor as the road narrows.
        const roadLane=clamp((x-sourceRoad.left)/sourceRoad.width,.06,.94);
        bullets.push({x,y,vx:0,vy:-velocity,life:1.5,targetId:null,targetX:x,targetY:66,roadLane});
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
      target.hitFlash=.14;
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
      if(b.roadLane!==undefined){
        const previousX=b.x;
        b.y+=b.vy*dt;
        if(b.y<=66){bullets.splice(i,1);continue;}
        b.x=roadXAtLane(b.y,b.roadLane);
        b.vx=dt>0?(b.x-previousX)/dt:0;
      }else{
        b.x+=b.vx*dt;b.y+=b.vy*dt;
      }
      b.life-=dt;

      // Track actual projectile centers while they are over the road surface.
      if(b.y>=66&&b.y<=H){
        const road=roadAt(b.y),margin=Math.min(9,road.width*.045);
        roadChecks++;
        if(b.x<road.left+margin||b.x>road.right-margin){
          roadViolations++;
          bullets.splice(i,1);
          continue;
        }
      }

      if(b.targetId!==null&&b.targetId!==undefined){
        const remaining=Math.hypot(b.targetX-b.x,b.targetY-b.y);
        if(remaining<=velocity*dt+6){
          const target=events.find(e=>e.id===b.targetId);
          if(target){
            applyProjectileHit(target);
            burst(b.targetX,b.targetY,C.lime,target.type==="target"?7:9);
          }
          bullets.splice(i,1);
          continue;
        }
      }
      if(b.life<=0||b.y<66||b.x< -30||b.x>W+30)bullets.splice(i,1);
    }
    canvas.dataset.roadChecks=String(roadChecks);
    canvas.dataset.roadViolations=String(roadViolations);
  }
  function drawBullets() {
    canvas.dataset.projectiles=String(bullets.length);
    ctx.save();
    bullets.forEach(b=>{
      ctx.save();ctx.translate(b.x,b.y);ctx.rotate(Math.atan2(b.vy,b.vx));
      ctx.strokeStyle="rgba(255,218,94,.98)";ctx.lineWidth=2.3;ctx.lineCap="round";
      ctx.shadowColor="#ffc83d";ctx.shadowBlur=6;
      ctx.beginPath();ctx.moveTo(-11,0);ctx.lineTo(-2,0);ctx.stroke();ctx.shadowBlur=0;
      ctx.fillStyle="#fff8ce";ctx.beginPath();ctx.ellipse(1,0,2.8,1.45,0,0,Math.PI*2);ctx.fill();
      ctx.restore();
    });
    ctx.restore();
  }
  function drawMuzzleFlashes() {
    ctx.save();ctx.globalCompositeOperation="lighter";
    muzzleFlashes.forEach(f=>{
      const alpha=clamp(f.life/f.max,0,1);
      ctx.save();ctx.globalAlpha=alpha;ctx.translate(f.x,f.y);
      ctx.fillStyle="#fff7bd";ctx.beginPath();ctx.moveTo(0,-7);ctx.lineTo(2.3,-1.5);ctx.lineTo(6,0);ctx.lineTo(1.7,1.7);ctx.lineTo(0,6);ctx.lineTo(-1.5,1.8);ctx.lineTo(-5,0);ctx.lineTo(-1.8,-1.7);ctx.closePath();ctx.fill();
      ctx.strokeStyle="rgba(255,210,75,.95)";ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(-4,0);ctx.lineTo(4,0);ctx.moveTo(0,3);ctx.lineTo(0,-5);ctx.stroke();
      ctx.restore();
    });
    ctx.restore();
  }
  function drawParticles() {
    particles.forEach(p=>{ctx.globalAlpha=clamp(p.life/p.max,0,1);ctx.fillStyle=p.color;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();});ctx.globalAlpha=1;
  }
  function frame(now) {
    const dt=lastFrame?Math.min((now-lastFrame)/1000,.05):0;lastFrame=now;
    update(dt);drawBackground(dt);drawRoad();drawEvents();drawSquad();drawBullets();drawMuzzleFlashes();drawParticles();syncHud();
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
