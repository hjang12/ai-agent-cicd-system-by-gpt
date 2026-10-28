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
    speedButtons: Array.from(document.querySelectorAll(".speed-button")),
    frame: $("gameFrame"), endKicker: $("endKicker"), endTitle: $("endTitle"),
    endCopy: $("endCopy"), endCount: $("endSoldierCount")
  };

  const H = 560, PLAYER_Y = 424, MAX_SOLDIERS = 1_000_000_000;
  const LANE_CENTERS = [1/6, 1/2, 5/6];
  const LANE_COUNT = LANE_CENTERS.length;
  let W = Math.max(220, Math.round(H * window.innerWidth / Math.max(1, window.innerHeight)));
  canvas.width = W;
  canvas.height = H;
  const MAX_REPRESENTATIVE_SOLDIERS = 72;
  const MAX_FORMATION_COLUMNS = 4;
  const FORMATION_SPACING = 25;
  const FORMATION_ROW_SPACING = 10.2;
  const FORMATION_MARGIN = 5;
  const MAX_FORMATION_ROWS = Math.floor((H - (PLAYER_Y - 25) - 14) / FORMATION_ROW_SPACING) + 1;
  const testMode = new URLSearchParams(location.search).get("testMode") === "1";
  const testBossCounterattack = testMode && new URLSearchParams(location.search).get("testBossCounterattack") === "1";
  const testShootableTarget = testMode && new URLSearchParams(location.search).get("testShootableTarget") === "1";
  const testProjectileRoadBounds = testMode && new URLSearchParams(location.search).get("testProjectileRoadBounds") === "1";
  const testAimedProjectileRoadBounds = testMode && new URLSearchParams(location.search).get("testAimedProjectileRoadBounds") === "1";
  const testCombatScaling = testMode ? new URLSearchParams(location.search).get("testCombatScaling") : null;
  const testLaneCombat = testMode ? new URLSearchParams(location.search).get("testLaneCombat") : null;
  const testEarlyEnemy = testMode && new URLSearchParams(location.search).get("testEarlyEnemy") === "1";
  const testLaneTransition = testMode && new URLSearchParams(location.search).get("testLaneTransition") === "1";
  const testDirectTarget = testMode && new URLSearchParams(location.search).get("testDirectTarget") === "1";
  const testTankBarrel = testMode && new URLSearchParams(location.search).get("testTankBarrel") === "1";
  const testFirstContactEnemy = testMode && new URLSearchParams(location.search).get("testFirstContactEnemy") === "1";
  const testEnemyFire = testMode && new URLSearchParams(location.search).get("testEnemyFire") === "1";
  const ENEMY_WAVE_SQUAD_RATIO = 0.35;
  const MAX_ENEMY_WAVE_SIZE = 210;
  const BOSS_HP_SQUAD_RATIO = 1.1;
  const MAX_BOSS_HP = 600;
  const COMBAT_LANE_TOLERANCE = 0.14;
  const TANK_BARREL_HITS = 500, TANK_DURATION = 10, TANK_DAMAGE = 4;
  const speed = testMode && !testEarlyEnemy && !testLaneTransition && !testDirectTarget && !testTankBarrel && !testFirstContactEnemy && !testEnemyFire ? 520 : 110;
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
    { type:"enemy", count:18, lane:5/6, label:"SCOUT SQUAD" },
    gate(add(10,"+10"), mult(2,"×2"), 4),
    gate(add(15,"+15"), pct(.5,"+50%"), 5),
    { type:"enemy", count:26, lane:1/6, label:"ENEMY UNIT" },
    shootTarget(add(1,"+1"), 6),
    { type:"enemy", count:32, lane:1/2, label:"HEAVY UNIT" },
    gate(add(12,"+12"), pct(.4,"+40%"), 7),
    gate(mult(2,"×2"), add(18,"+18"), 8),
    { type:"barrel", hitsRequired:TANK_BARREL_HITS, label:"TANK BARREL" },
    { type:"boss", hp:76, label:"FINAL COMMANDER" }
  ];

  let mode="ready", soldiers=12, resolved=0, nextIndex=0, events=[];
  let fireClock=0, attackClock=0, lane=.5, targetLane=.5, offset=0, lastFrame=0;
  let speedMultiplier=1, simulationSeconds=0, tankTimeRemaining=0, selectedTargetId=null;
  let message="Choose your route. The squad is waiting.", bullets=[], particles=[], muzzleFlashes=[];
  let totalEnemyHits=0, totalEnemyHitsBeforeEngagement=0, totalBossHits=0, totalTargetHits=0, totalSelectedTargetHits=0, lastTargetValue=0, lastTankBarrelHits=0;
  let roadChecks=0, roadViolations=0, volleySequence=0, firedShotsByLane=[0,0,0];
  let lastCombatTargetId=null, lastCombatAlignment=null;
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const rand=(a,b)=>a+Math.random()*(b-a);
  function nearestLaneIndex(position) {
    let best=0, distance=Infinity;
    for(let i=0;i<LANE_CENTERS.length;i++){
      const next=Math.abs(position-LANE_CENTERS[i]);
      if(next<distance){best=i;distance=next;}
    }
    return best;
  }
  function laneFireWeights(position) {
    const p=clamp(position,LANE_CENTERS[0],LANE_CENTERS[LANE_COUNT-1]);
    if(p<=LANE_CENTERS[1]){
      const t=clamp((p-LANE_CENTERS[0])/(LANE_CENTERS[1]-LANE_CENTERS[0]),0,1);
      return [1-t,t,0];
    }
    const t=clamp((p-LANE_CENTERS[1])/(LANE_CENTERS[2]-LANE_CENTERS[1]),0,1);
    return [0,1-t,t];
  }
  function sampleLaneIndex(weights,shotIndex,shotCount,sequence) {
    // Rotating, evenly spaced samples keep each volley close to the requested ratios.
    const phase=(sequence*0.38196601125)%1;
    const sample=((shotIndex+0.5)/shotCount+phase)%1;
    if(sample<weights[0])return 0;
    if(sample<weights[0]+weights[1])return 1;
    return 2;
  }
  function syncFireMetrics() {
    const weights=laneFireWeights(lane);
    canvas.dataset.laneCount=String(LANE_COUNT);
    canvas.dataset.playerLanePosition=lane.toFixed(4);
    canvas.dataset.fireLaneWeights=weights.map(value=>value.toFixed(3)).join(",");
    canvas.dataset.firedShotsLane1=String(firedShotsByLane[0]);
    canvas.dataset.firedShotsLane2=String(firedShotsByLane[1]);
    canvas.dataset.firedShotsLane3=String(firedShotsByLane[2]);
  }
  function resetFireMetrics() {
    volleySequence=0;
    firedShotsByLane=[0,0,0];
    syncFireMetrics();
  }
  function syncSpeedControls() {
    canvas.dataset.gameSpeed=String(speedMultiplier);
    ui.speedButtons.forEach(button=>{
      const active=Number(button.dataset.speed)===speedMultiplier;
      button.setAttribute("aria-pressed",String(active));
      button.classList.toggle("is-active",active);
    });
  }
  function setGameSpeed(value) {
    const next=Number(value);
    if(![1,2,3,4].includes(next))return;
    speedMultiplier=next;
    syncSpeedControls();
  }

  function roadAt(y) {
    const t=clamp((y-66)/(H-66),0,1), width=lerp(W*220/960,W*880/960,t);
    return {left:(W-width)/2,right:(W+width)/2,width,t};
  }
  function roadXAtLane(y,lanePosition) {
    const road=roadAt(y);
    return road.left+road.width*clamp(lanePosition,.06,.94);
  }
  function squadFormation() {
    const muzzleRoad=roadAt(PLAYER_Y-47);
    // Four well-separated columns on desktop; troop scale and spacing shrink on narrow screens.
    const laneWidth=muzzleRoad.width/LANE_COUNT;
    const soldierScale=clamp(laneWidth/150,.36,1);
    const soldierHalfWidth=24*soldierScale;
    const centerSpread=Math.max(0,laneWidth/2-FORMATION_MARGIN-soldierHalfWidth);
    const preferredSpacing=FORMATION_SPACING*soldierScale;
    const possibleCols=Math.floor((2*centerSpread)/Math.max(1,preferredSpacing))+1;
    const cols=clamp(possibleCols,2,MAX_FORMATION_COLUMNS);
    const spacing=cols>1?Math.min(preferredSpacing,(2*centerSpread)/(cols-1)):0;
    const halfWidth=((cols-1)/2)*spacing+soldierHalfWidth;
    const count=Math.min(soldiers,MAX_REPRESENTATIVE_SOLDIERS,cols*MAX_FORMATION_ROWS);
    const rowSpacing=FORMATION_ROW_SPACING;
    const desiredCenter=muzzleRoad.left+muzzleRoad.width*clamp(lane,.06,.94);
    const minCenter=muzzleRoad.left+halfWidth+FORMATION_MARGIN;
    const maxCenter=muzzleRoad.right-halfWidth-FORMATION_MARGIN;
    const centerX=clamp(desiredCenter,minCenter,maxCenter);
    const laneIndex=nearestLaneIndex(lane);
    return {count,cols,spacing,rowSpacing,centerX,halfWidth,laneIndex,laneName:String(laneIndex+1),soldierScale};
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
    else if(events.some(e=>e.type==="barrel")) ui.enemy.textContent="TANK BARREL";
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
    fireClock=testMode?0.18:0.3; attackClock=0; lane=.5; targetLane=.5; bullets=[]; particles=[]; muzzleFlashes=[];
    tankTimeRemaining=0; selectedTargetId=null; lastTankBarrelHits=0;
    totalEnemyHits=0; totalEnemyHitsBeforeEngagement=0; totalBossHits=0; totalTargetHits=0; totalSelectedTargetHits=0; lastTargetValue=0; roadChecks=0; roadViolations=0;
    lastCombatTargetId=null; lastCombatAlignment=null; resetFireMetrics();
    simulationSeconds=0; canvas.dataset.simulationSeconds="0";
    canvas.dataset.combatLaneAligned="none"; canvas.dataset.combatTargetLane="";
    canvas.dataset.projectiles="0"; canvas.dataset.straightProjectiles="0"; canvas.dataset.playerBulletsStraight="true"; canvas.dataset.enemyProjectiles="0"; canvas.dataset.enemyProjectileHits="0"; canvas.dataset.enemyVisibleCount="0"; canvas.dataset.enemyCount="0"; canvas.dataset.enemyWaveInitialCount="0"; canvas.dataset.enemyHits="0"; canvas.dataset.enemyHitsBeforeEngagement="0"; canvas.dataset.earlyEnemyHitY=""; canvas.dataset.firstEnemyHitSeconds=""; canvas.dataset.enemySpawnSeconds="0"; canvas.dataset.enemyEngagedId=""; canvas.dataset.enemyEngagedCount=""; canvas.dataset.bossHits="0"; canvas.dataset.bossMaxHp="0"; canvas.dataset.shootTargetHits="0"; canvas.dataset.shootTargetValue="0"; canvas.dataset.selectedTargetHits="0"; canvas.dataset.selectedTargetId=""; canvas.dataset.selectedTargetType=""; canvas.dataset.tankBarrelHits="0"; canvas.dataset.tankBarrelHitsRequired=String(TANK_BARREL_HITS); canvas.dataset.tankMode="false"; canvas.dataset.tankTimeRemaining="0"; canvas.dataset.tankDamage=String(TANK_DAMAGE); canvas.dataset.roadChecks="0"; canvas.dataset.roadViolations="0";
    syncSpeedControls();
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
    }else if(testDirectTarget){
      soldiers=60; lane=targetLane=.5;
      events=[
        {type:"enemy",count:1000,initialCount:1000,lane:1/6,label:"LEFT TEST",id:31,y:160,engaged:false,resolved:false},
        {type:"enemy",count:1000,initialCount:1000,lane:5/6,label:"RIGHT TEST",id:32,y:160,engaged:false,resolved:false}
      ];
      nextIndex=ROUND.length;
    }else if(testFirstContactEnemy){
      soldiers=60;lane=targetLane=.5;
      const source=ROUND.find(e=>e.type==="enemy");
      events=source?[{...source,lane:.5,count:18,initialCount:18,id:3,y:96,engaged:false,resolved:false}]:[];
      nextIndex=ROUND.length;
    }else if(testEnemyFire){
      soldiers=60;lane=targetLane=.5;
      events=[{type:"enemy",count:100,initialCount:100,lane:.5,label:"ENEMY FIRE TEST",id:41,y:PLAYER_Y-181,engaged:true,resolved:false,attackClock:0}];
      nextIndex=ROUND.length;
    }else if(testTankBarrel){
      soldiers=1000;
      events=[{type:"barrel",hits:0,hitsRequired:TANK_BARREL_HITS,id:50,y:PLAYER_Y-150,engaged:true,resolved:false,label:"TANK BARREL"}];
      nextIndex=ROUND.length;
    }else if(testCombatScaling==="enemy"){
      soldiers=1000;
      const source=ROUND.find(e=>e.type==="enemy");
      const waveCount=source?Math.max(source.count,Math.min(MAX_ENEMY_WAVE_SIZE,Math.ceil(soldiers*ENEMY_WAVE_SQUAD_RATIO))):0;
      events=source?[{...source,count:waveCount,initialCount:waveCount,id:3,y:PLAYER_Y-181,engaged:false,resolved:false}]:[];
      nextIndex=ROUND.length;
    }else if(testCombatScaling==="boss"){
      soldiers=400;
      events=[{...ROUND[ROUND.length-1],hp:76,id:ROUND.length-1,y:PLAYER_Y-125,engaged:false,resolved:false}];
      nextIndex=ROUND.length;
    }else if(testLaneCombat==="matched"||testLaneCombat==="mismatched"){
      soldiers=60;
      const enemyLane=5/6;
      lane=targetLane=testLaneCombat==="matched"?enemyLane:.5;
      events=[{type:"enemy",count:24,lane:enemyLane,label:"LANE TEST",id:3,y:PLAYER_Y-181,engaged:false,resolved:false}];
      nextIndex=ROUND.length;
    }else if(testEarlyEnemy){
      soldiers=60;
      lane=targetLane=LANE_CENTERS[2];
      const source=ROUND.find(e=>e.type==="enemy");
      events=source?[{...source,lane:LANE_CENTERS[2],count:100,initialCount:100,id:3,y:96,engaged:false,resolved:false}]:[];
      nextIndex=ROUND.length;
    }else if(testLaneTransition){
      soldiers=60;
      lane=targetLane=LANE_CENTERS[0];
      events=[
        {type:"enemy",count:100,lane:LANE_CENTERS[0],label:"LANE ONE TEST",id:21,y:120,engaged:false,resolved:false},
        {type:"enemy",count:100,lane:LANE_CENTERS[1],label:"LANE TWO TEST",id:22,y:120,engaged:false,resolved:false}
      ];
      nextIndex=ROUND.length;
    }else{
      events=[{...ROUND[0],id:0,y:96,engaged:false,resolved:false}];
    }
    fireClock=testMode?0.18:0.3; attackClock=0;
    if(!testProjectileRoadBounds&&!testAimedProjectileRoadBounds&&!testLaneCombat&&!testEarlyEnemy&&!testLaneTransition&&!testDirectTarget){lane=.5;targetLane=.5;}
    bullets=[]; particles=[]; muzzleFlashes=[];
    totalEnemyHits=0; totalEnemyHitsBeforeEngagement=0; totalBossHits=0; totalTargetHits=0; totalSelectedTargetHits=0; lastTargetValue=0; roadChecks=0; roadViolations=0; tankTimeRemaining=0; selectedTargetId=null; lastTankBarrelHits=0; resetFireMetrics();
    lastCombatTargetId=null; lastCombatAlignment=null;
    simulationSeconds=0; canvas.dataset.simulationSeconds="0";
    canvas.dataset.enemyProjectileHits="0";canvas.dataset.enemyProjectiles="0";canvas.dataset.straightProjectiles="0";canvas.dataset.playerBulletsStraight="true";
    canvas.dataset.combatLaneAligned="none"; canvas.dataset.combatTargetLane="";
    canvas.dataset.projectiles="0"; canvas.dataset.straightProjectiles="0"; canvas.dataset.playerBulletsStraight="true"; canvas.dataset.enemyProjectiles="0"; canvas.dataset.enemyProjectileHits="0"; canvas.dataset.enemyVisibleCount="0"; canvas.dataset.enemyCount="0"; canvas.dataset.enemyWaveInitialCount="0"; canvas.dataset.enemyHits="0"; canvas.dataset.enemyHitsBeforeEngagement="0"; canvas.dataset.earlyEnemyHitY=""; canvas.dataset.firstEnemyHitSeconds=""; canvas.dataset.enemySpawnSeconds="0"; canvas.dataset.enemyEngagedId=""; canvas.dataset.enemyEngagedCount=""; canvas.dataset.bossHits="0"; canvas.dataset.bossMaxHp="0"; canvas.dataset.shootTargetHits="0"; canvas.dataset.shootTargetValue="0"; canvas.dataset.selectedTargetHits="0"; canvas.dataset.selectedTargetId=""; canvas.dataset.selectedTargetType=""; canvas.dataset.tankBarrelHits="0"; canvas.dataset.tankBarrelHitsRequired=String(TANK_BARREL_HITS); canvas.dataset.tankMode="false"; canvas.dataset.tankTimeRemaining="0"; canvas.dataset.tankDamage=String(TANK_DAMAGE); canvas.dataset.roadChecks="0"; canvas.dataset.roadViolations="0";
    syncSpeedControls();
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
    const event={...source,...(source.effect?{effect:{...source.effect}}:{}),id:nextIndex,y:96,engaged:false,resolved:false};
    if(event.type==="enemy"){
      // Set the wave's starting size once at appearance; long-range hits must never be healed back at engagement.
      event.count=Math.max(event.count,Math.min(MAX_ENEMY_WAVE_SIZE,Math.ceil(soldiers*ENEMY_WAVE_SQUAD_RATIO)));
      event.initialCount=event.count;
      canvas.dataset.enemyWaveInitialCount=String(event.initialCount);
    }
    if(event.type==="enemy"){
      canvas.dataset.enemySpawnSeconds=simulationSeconds.toFixed(3);
      fireClock=Math.max(fireClock,testMode?0.18:0.3);
    }
    if(event.type==="barrel"){
      event.hits=0;event.hitsRequired=event.hitsRequired||TANK_BARREL_HITS;
      lastTankBarrelHits=0;canvas.dataset.tankBarrelHits="0";
    }
    events.push(event);
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
    if(selectedTargetId===e.id)selectedTargetId=null;
    say("Target "+e.index+": "+appliedLabel+" applied after "+(e.hits||0)+" hits.");
    const road=roadAt(PLAYER_Y);burst(road.left+road.width*.5,PLAYER_Y-14,soldiers>=before?C.lime:C.red,18);
  }
  function resolveBarrel(e) {
    if(!events.includes(e)||e.resolved)return;
    e.resolved=true;resolved++;
    lastTankBarrelHits=e.hitsRequired;
    tankTimeRemaining=TANK_DURATION;selectedTargetId=null;
    events=events.filter(item=>item!==e);
    canvas.dataset.tankBarrelHits=String(lastTankBarrelHits);
    const road=roadAt(e.y);burst(road.left+road.width*.5,e.y,C.lime,38);
    say("TANK UNLOCKED · "+TANK_DURATION+"s of powered fire!");
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
    // Pointer position maps continuously to the road; firing weights blend between adjacent lanes.
    targetLane=clamp((x-road.left)/road.width,LANE_CENTERS[0],LANE_CENTERS[LANE_COUNT-1]);
  }
  function isTargetSelectable(e) {
    if(!e||e.y<=66||e.y>=PLAYER_Y+80)return false;
    if(e.type==="enemy")return e.count>0;
    if(e.type==="target")return !e.resolved;
    if(e.type==="barrel")return !e.resolved&&(e.hits||0)<(e.hitsRequired||TANK_BARREL_HITS);
    if(e.type==="boss")return !!e.engaged&&e.hp>0;
    return false;
  }
  function activeSelectedTarget() {
    const target=selectedTargetId===null?null:events.find(e=>e.id===selectedTargetId);
    if(target&&isTargetSelectable(target))return target;
    selectedTargetId=null;return null;
  }
  function isSelectedTarget(e) { return selectedTargetId!==null&&e.id===selectedTargetId; }
  function selectTarget(target) {
    selectedTargetId=target?target.id:null;
    if(target){
      if(target.type==="enemy")targetLane=clamp(target.lane,LANE_CENTERS[0],LANE_CENTERS[LANE_COUNT-1]);
      else if(target.type==="barrel"||target.type==="boss")targetLane=.5;
      say("Target locked: "+(target.label||target.type)+". Steering into its line of fire.");
    }else say("Target lock cleared. Auto-fire resumed.");
  }
  function targetAtPoint(event) {
    const rect=canvas.getBoundingClientRect();
    const x=(event.clientX-rect.left)/rect.width*W,y=(event.clientY-rect.top)/rect.height*H;
    for(let i=events.length-1;i>=0;i--){
      const e=events[i];if(!isTargetSelectable(e))continue;
      if(e.type==="enemy"){
        const road=roadAt(e.y),cx=road.left+road.width*e.lane,s=.58+road.t*.92;
        if(x>=cx-78*s&&x<=cx+78*s&&y>=e.y-52*s&&y<=e.y+58*s)return e;
      }else if(e.type==="target"){
        const g=shootTargetGeometry(e);
        if(x>=g.x-5&&x<=g.x+g.w+5&&y>=g.y-10&&y<=g.y+g.h+10)return e;
      }else if(e.type==="barrel"){
        const g=barrelGeometry(e);
        if(x>=g.x-8&&x<=g.x+g.w+8&&y>=g.y-28&&y<=g.y+g.h+8)return e;
      }else if(e.type==="boss"){
        const road=roadAt(e.y),cx=road.left+road.width/2;
        if(x>=cx-65&&x<=cx+65&&y>=e.y-88&&y<=e.y+55)return e;
      }
    }
    return null;
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

    // Two perspective dividers make three continuous lanes readable at every screen size.
    const laneTop=roadAt(66),laneBottom=roadAt(H);
    ctx.strokeStyle="rgba(255,255,255,.82)";ctx.lineWidth=2.5;ctx.setLineDash([16,17]);ctx.lineDashOffset=-offset*1.8;
    for(const boundary of [1/3,2/3]){
      ctx.beginPath();
      ctx.moveTo(laneTop.left+laneTop.width*boundary,66);
      ctx.lineTo(laneBottom.left+laneBottom.width*boundary,H);
      ctx.stroke();
    }
    ctx.setLineDash([]);

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

  function drawTank(x,y,scale=1) {
    ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);
    ctx.fillStyle="rgba(14,43,63,.22)";ctx.beginPath();ctx.ellipse(0,18,43,13,0,0,Math.PI*2);ctx.fill();
    roundRect(-36,-18,12,43,5,"#273644","#142536");roundRect(24,-18,12,43,5,"#273644","#142536");
    for(let i=-13;i<=15;i+=9){ctx.fillStyle="#91a4b5";ctx.beginPath();ctx.arc(-30,i,2.6,0,Math.PI*2);ctx.arc(30,i,2.6,0,Math.PI*2);ctx.fill();}
    const hull=ctx.createLinearGradient(-25,-23,27,22);hull.addColorStop(0,"#93a9b8");hull.addColorStop(.45,"#586e7d");hull.addColorStop(1,"#324756");
    roundRect(-25,-22,50,40,7,hull,"#263d4e");roundRect(-16,-16,32,24,5,"#6b8290","#31495a");
    roundRect(-6,-31,12,25,3,"#3a4f60","#1e3344");roundRect(-3,-51,6,29,2,"#1d3345","#0e2334");
    roundRect(-20,6,40,7,2,"#c7d3dc","#445969");
    ctx.fillStyle="#ffd34d";ctx.beginPath();ctx.arc(0,-25,3,0,Math.PI*2);ctx.fill();ctx.restore();
  }

  function drawSquad() {
    const formation=squadFormation(),road=roadAt(PLAYER_Y),x=formation.centerX;
    const formationRows=Math.ceil(formation.count/formation.cols);
    canvas.dataset.squadColumns=String(formation.cols);
    canvas.dataset.squadRows=String(formationRows);
    canvas.dataset.squadVisibleCount=String(formation.count);
    canvas.dataset.squadLane=formation.laneName;
    canvas.dataset.squadCenterX=String(formation.centerX);
    canvas.dataset.squadHalfWidth=String(formation.halfWidth);
    const shadowWidth=Math.min(road.width*.22,formation.halfWidth+10);
    const shadowCenterY=PLAYER_Y+18+Math.min(45,(formationRows-1)*formation.rowSpacing*.35);
    const shadowHeight=Math.min(70,24+formation.rowSpacing*Math.max(0,formationRows-1)*.5);
    ctx.fillStyle="rgba(28,130,237,.15)";ctx.beginPath();ctx.ellipse(x,shadowCenterY,shadowWidth,shadowHeight,0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle="rgba(23,117,219,.24)";ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(x,shadowCenterY,shadowWidth,shadowHeight,0,0,Math.PI*2);ctx.stroke();

    // Use the same formation geometry for rendered soldiers and their muzzle positions.
    for(let i=0;i<formation.count;i++){
      const p=squadSoldierPosition(formation,i);drawTrooper(p.x,p.y,formation.soldierScale,false);
    }
    if(tankTimeRemaining>0){
      drawTank(x,PLAYER_Y-59,clamp((road.width/LANE_COUNT)/90,.58,1));
      const label="TANK ACTIVE · "+Math.ceil(tankTimeRemaining)+"s";
      ctx.font="900 10px ui-sans-serif,system-ui";ctx.textAlign="center";ctx.textBaseline="middle";
      const labelWidth=ctx.measureText(label).width+16;
      roundRect(x-labelWidth/2,PLAYER_Y-112,labelWidth,20,6,"rgba(19,54,72,.94)","#ffd34d");
      ctx.fillStyle="#ffe37c";ctx.fillText(label,x,PLAYER_Y-102);ctx.textBaseline="alphabetic";
    }
    // Keep the road unobstructed; squad size is already visible in the HUD.
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
  function barrelGeometry(e) {
    const road=roadAt(e.y),s=.58+road.t*.62,w=82*s,h=78*s;
    return {road,s,w,h,x:road.left+(road.width-w)/2,y:e.y-h/2};
  }
  function drawTargetReticle(x,y,w,h) {
    ctx.save();ctx.strokeStyle="#ffe36a";ctx.lineWidth=2.4;ctx.setLineDash([5,3]);
    roundRect(x-5,y-5,w+10,h+10,5,null,"#ffe36a");ctx.setLineDash([]);ctx.restore();
  }
  function drawShootTarget(e) {
    const g=shootTargetGeometry(e);
    drawGatePanel(g.x,g.y,g.w,g.h,e.effect,g.s,"SHOOT TO BOOST");
    if((e.hitFlash||0)>0){ctx.save();ctx.strokeStyle="rgba(255,255,255,.9)";ctx.lineWidth=2+g.s;ctx.strokeRect(g.x-3,g.y-3,g.w+6,g.h+6);ctx.restore();}
    if(isSelectedTarget(e))drawTargetReticle(g.x,g.y,g.w,g.h);
  }
  function drawTankBarrel(e) {
    const g=barrelGeometry(e),x=g.x,y=g.y,w=g.w,h=g.h,s=g.s;ctx.save();
    ctx.fillStyle="rgba(26,54,74,.25)";ctx.beginPath();ctx.ellipse(x+w/2,y+h*.91,w*.65,h*.16,0,0,Math.PI*2);ctx.fill();
    const steel=ctx.createLinearGradient(x,y,x+w,y+h);steel.addColorStop(0,"#d4e0e7");steel.addColorStop(.28,"#758b9a");steel.addColorStop(.65,"#465a68");steel.addColorStop(1,"#263c4b");
    roundRect(x+w*.14,y+h*.12,w*.72,h*.82,8*s,steel,"#243a4c");
    ctx.fillStyle="#263c4b";ctx.beginPath();ctx.ellipse(x+w/2,y+h*.14,w*.36,h*.12,0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle="#e2eaf0";ctx.lineWidth=2*s;ctx.beginPath();ctx.ellipse(x+w/2,y+h*.14,w*.28,h*.08,0,0,Math.PI*2);ctx.stroke();
    roundRect(x+w*.1,y+h*.36,w*.8,8*s,2*s,"#ffd34d","#614a18");roundRect(x+w*.1,y+h*.7,w*.8,7*s,2*s,"#1c2a37","#141e29");
    for(let k=0;k<5;k++){const sx=x+w*(.15+k*.15),sy=y+h*.38;ctx.strokeStyle="#273746";ctx.lineWidth=2*s;ctx.beginPath();ctx.moveTo(sx,sy+6*s);ctx.lineTo(sx+7*s,sy);ctx.stroke();}
    ctx.fillStyle="#fff";ctx.textAlign="center";ctx.textBaseline="middle";
    const label="TANK BARREL  "+Math.max(0,(e.hitsRequired||TANK_BARREL_HITS)-(e.hits||0))+" HITS LEFT";
    ctx.font="900 "+Math.max(7,Math.round(9*s))+"px ui-sans-serif,system-ui";
    const labelW=Math.max(w+18,ctx.measureText(label).width+14);
    roundRect(x+w/2-labelW/2,y-25*s,labelW,17*s,4*s,(e.hitFlash||0)>.01?"#fff2ab":"rgba(255,255,255,.97)","#bd7b19");
    ctx.fillStyle="#7a4a08";ctx.fillText(label,x+w/2,y-16.5*s);
    const ratio=clamp((e.hits||0)/(e.hitsRequired||TANK_BARREL_HITS),0,1);
    roundRect(x-2,y+h+3*s,w+4,6*s,3*s,"rgba(255,255,255,.92)","#5b6d7b");if(ratio>0)roundRect(x,y+h+4*s,w*ratio,4*s,2*s,"#ffd34d");
    ctx.restore();if(isSelectedTarget(e))drawTargetReticle(x-4,y-27*s,w+8,h+34*s);
  }
  function visibleEnemyCount(e) {
    const count=Math.max(0,Math.round(Number(e.count)||0));
    if(count<=0)return 0;
    if(!Number.isFinite(e.initialCount)||e.initialCount<=0)e.initialCount=count;
    e.initialCount=Math.max(count,Math.round(e.initialCount));
    if(e.initialCount<=32)return Math.min(32,count);
    return Math.min(32,Math.max(1,Math.round(32*count/e.initialCount)));
  }
  function drawEnemy(e) {
    const r=roadAt(e.y),x=r.left+r.width*e.lane,s=.58+r.t*.92;
    ctx.fillStyle="rgba(222,48,59,.14)";ctx.beginPath();ctx.ellipse(x,e.y+13,69*s,20*s,0,0,Math.PI*2);ctx.fill();
    const n=visibleEnemyCount(e);
    canvas.dataset.enemyVisibleCount=String(n);
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
    if(isSelectedTarget(e))drawTargetReticle(x-77*s,e.y-43*s,154*s,93*s);
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
    if(isSelectedTarget(e))drawTargetReticle(x-52*s,e.y-75*s,104*s,125*s);
  }

  function drawEvents() {
    events.forEach(e=>{
      if(e.type==="gate"&&e.y>62&&e.y<H+60)drawGate(e);
      else if(e.type==="target"&&e.y>62&&e.y<H+60)drawShootTarget(e);
      else if(e.type==="enemy"&&e.y>66&&e.y<PLAYER_Y+80)drawEnemy(e);
      else if(e.type==="barrel"&&e.y>66&&e.y<PLAYER_Y+80)drawTankBarrel(e);
      else if(e.type==="boss")drawBoss(e);
    });
  }
  function update(dt) {
    for(let i=particles.length-1;i>=0;i--){const p=particles[i];p.x+=p.vx*dt;p.y+=p.vy*dt;p.vx*=Math.max(0,1-dt*1.6);p.vy*=Math.max(0,1-dt*1.6);p.life-=dt;if(p.life<=0)particles.splice(i,1);}
    for(let i=muzzleFlashes.length-1;i>=0;i--){muzzleFlashes[i].life-=dt;if(muzzleFlashes[i].life<=0)muzzleFlashes.splice(i,1);}
    if(mode!=="running")return;
    tankTimeRemaining=Math.max(0,tankTimeRemaining-dt);
    simulationSeconds+=dt;
    canvas.dataset.simulationSeconds=simulationSeconds.toFixed(3);
    // Keep the run readable: do not overlap gates or spawn the next event while a fight is active.
    // The next obstacle appears immediately after the current event has been resolved.
    const combatInProgress=events.some(e=>(e.type==="enemy"||e.type==="boss"||e.type==="barrel")&&e.engaged);
    if(!combatInProgress&&events.length===0&&nextIndex<ROUND.length)spawnNext();
    lane+=(targetLane-lane)*Math.min(1,dt*4.8);
    syncFireMetrics();
    for(let i=events.length-1;i>=0;i--){
      const e=events[i];
      if(e.type==="enemy"&&e.count<=0){resolveEnemy(e);events.splice(i,1);continue;}
      if(e.type==="boss"&&e.engaged){updateBoss(e,dt);if(mode!=="running")return;continue;}
      if(e.type==="enemy"&&e.engaged){
        if(e.count<=0){resolveEnemy(e);events.splice(i,1);continue;}
        updateEnemyWave(e,dt);
        if(mode!=="running")return;
        if(e.count<=0){resolveEnemy(e);events.splice(i,1);}
        continue;
      }
      if(e.type==="barrel"&&e.engaged)continue;
      e.y+=speed*dt;
      if(e.type==="gate"&&e.y>=PLAYER_Y-24){resolveGate(e);events.splice(i,1);continue;}
      if(e.type==="target"&&e.y>=PLAYER_Y-24){resolveShootTarget(e);events.splice(i,1);continue;}
      if(e.type==="barrel"&&e.y>=PLAYER_Y-150){
        e.engaged=true;e.y=PLAYER_Y-150;e.hitFlash=0;
        say("Tank barrel ahead. Focus fire to unlock a tank.");continue;
      }
      if(e.type==="enemy"&&e.y>=PLAYER_Y-180){
        if(!Number.isFinite(e.initialCount))e.initialCount=e.count;
        canvas.dataset.enemyWaveInitialCount=String(e.initialCount);
        canvas.dataset.enemyEngagedId=String(e.id);
        canvas.dataset.enemyEngagedCount=String(e.count);
        // Stop where the enemy reaches the combat line; do not teleport it into bullets already in flight.
        e.engaged=true;e.attackClock=0;e.hitFlash=0;
        say(e.label+" engaged. Keep steering to adjust the firing spread.");
        continue;
      }
      if(e.type==="boss"&&e.y>=PLAYER_Y-124){e.hp=Math.max(e.hp,Math.min(MAX_BOSS_HP,Math.round(soldiers*BOSS_HP_SQUAD_RATIO)));e.engaged=true;e.y=PLAYER_Y-119;e.maxHp=e.hp;canvas.dataset.bossMaxHp=String(e.maxHp);attackClock=0;say("Final commander engaged. Auto-fire on target.");}
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
  function spawnEnemyVolley(event,shotCount,commander=false) {
    if(mode!=="running"||soldiers<=0)return;
    const count=Math.max(1,Math.min(5,Math.floor(shotCount)));
    const laneCenter=commander ? .5 : event.lane;
    const y=event.y+(commander?22:18);
    for(let i=0;i<count;i++){
      const spread=count===1?0:(i-(count-1)/2)*.022;
      const roadLane=clamp(laneCenter+spread,.06,.94);
      const x=roadXAtLane(y,roadLane);
      bullets.push({team:"enemy",x,y,vx:0,vy:commander?720:620,roadLane,life:2.4,targetId:null,straight:true});
      muzzleFlashes.push({x,y,life:.11,max:.11,team:"enemy"});
    }
    canvas.dataset.enemyProjectiles=String(bullets.filter(b=>b.team==="enemy").length);
  }
  function updateEnemyWave(e,dt) {
    e.hitFlash=Math.max(0,(e.hitFlash||0)-dt);
    e.attackClock=(e.attackClock||0)+dt;
    const interval=1.05;
    if(e.attackClock<interval)return;
    e.attackClock-=interval;
    const shots=Math.min(2,Math.max(1,Math.ceil(Math.min(soldiers,e.count)*0.03)));
    spawnEnemyVolley(e,shots);
    say(e.label+" fires "+shots+" rounds — move out of the firing line.");
  }
  function updateBoss(e,dt) {
    e.hitFlash=Math.max(0,(e.hitFlash||0)-dt);
    if(e.hp<=0){resolved++;events=events.filter(item=>item!==e);finishRun("won");return;}
    attackClock+=dt;
    if(attackClock>=(testMode?0.8:1.05)){
      attackClock-=testMode?0.8:1.05;
      const shots=Math.min(soldiers,soldiers<24?2:Math.max(1,Math.round(soldiers*.015)));
      spawnEnemyVolley(e,shots,true);
      say("Commander fires back — dodge the central firing line.");
    }
    if(e.hp<=0){resolved++;events=events.filter(item=>item!==e);finishRun("won");}
  }
  function projectileTargetPoint(target,sourceX,sourceY,projectileVelocity=980) {
    if(target.type==="barrel"){const g=barrelGeometry(target);return {x:g.x+g.w/2,y:g.y+g.h/2};}
    if(target.type==="boss"){
      const road=roadAt(target.y);
      return {x:road.left+road.width/2,y:target.y-27};
    }
    if(target.type==="target"){
      const initial=shootTargetGeometry(target);
      const distance=Math.max(0,sourceY-(initial.y+initial.h/2));
      const travelTime=distance/(projectileVelocity+speed);
      const predictedEventY=Math.min(target.y+speed*travelTime,PLAYER_Y-24);
      const future=shootTargetGeometry({...target,y:predictedEventY});
      return {x:future.x+future.w/2,y:future.y+future.h/2};
    }
    const targetY=target.engaged
      ?target.y
      :Math.min(target.y+speed*Math.max(0,sourceY-target.y)/(projectileVelocity+speed),PLAYER_Y-180);
    const road=roadAt(targetY);
    return {x:road.left+road.width*target.lane,y:targetY};
  }
  function fireVolley(fixedTarget) {
    const formation=squadFormation(),velocity=980;
    const shotCount=Math.min(32,3+Math.floor(soldiers/18),formation.count);
    for(let i=0;i<shotCount;i++){
      const index=shotCount===1?Math.floor((formation.count-1)/2):Math.round(i*(formation.count-1)/(shotCount-1));
      const soldier=squadSoldierPosition(formation,index),y=soldier.y-22;
      const sourceRoad=roadAt(y),x=clamp(soldier.x+6,sourceRoad.left+10,sourceRoad.right-10);
      muzzleFlashes.push({x:x+1,y:y-1,life:.075,max:.075,team:"player"});
      const sourceLane=clamp((x-sourceRoad.left)/sourceRoad.width,.06,.94);
      firedShotsByLane[nearestLaneIndex(sourceLane)]++;
      if(fixedTarget){
        // Pick one direction at launch; the projectile never steers or teleports to a target.
        const aim=projectileTargetPoint(fixedTarget,x,y,velocity);
        const dx=aim.x-x,dy=aim.y-y,dist=Math.hypot(dx,dy)||1;
        bullets.push({team:"player",x,y,vx:dx/dist*velocity,vy:dy/dist*velocity,life:2.4,targetId:null,straight:true});
      }else{
        // Default fire runs forward along its lane, independent of target positions.
        const roadLane=clamp(sourceLane,.06,.94);
        bullets.push({team:"player",x,y,vx:0,vy:-velocity,roadLane,life:2.4,targetId:null,straight:true});
      }
    }
    syncFireMetrics();
  }
  function projectileCrossesY(previousY,nextY,top,bottom) {
    const low=Math.min(previousY,nextY),high=Math.max(previousY,nextY);
    return high>=top&&low<=bottom;
  }
  function projectileXAt(b,y,previousY,nextY,previousX,nextX) {
    if(b.roadLane!==undefined)return roadXAtLane(y,b.roadLane);
    const dy=nextY-previousY;
    const t=Math.abs(dy)<1e-9?0:clamp((y-previousY)/dy,0,1);
    return previousX+(nextX-previousX)*t;
  }
  function findPlayerProjectileHit(b,previousY,nextY,previousX,nextX) {
    const low=Math.min(previousY,nextY),high=Math.max(previousY,nextY);
    for(let j=events.length-1;j>=0;j--){
      const e=events[j];
      if(e.type==="enemy"&&e.count>0){
        const road=roadAt(e.y),scale=.58+road.t*.92,n=visibleEnemyCount(e),cols=6;
        for(let k=0;k<n;k++){
          const row=Math.floor(k/cols),col=k%cols,inRow=Math.min(cols,n-row*cols),rowOffset=(cols-inRow)/2;
          const sx=road.left+road.width*e.lane+(col+rowOffset-(cols-1)/2)*18*scale+(row%2?2.2*scale:0);
          const sy=e.y+row*12*scale,top=sy-21*scale,bottom=sy+7*scale;
          if(!projectileCrossesY(previousY,nextY,top,bottom))continue;
          const impactY=clamp((Math.max(low,top)+Math.min(high,bottom))/2,low,high);
          if(Math.abs(projectileXAt(b,impactY,previousY,nextY,previousX,nextX)-sx)<=8*scale)return {target:e,x:sx,y:impactY};
        }
      }else if(e.type==="target"&&!e.resolved){
        const g=shootTargetGeometry(e),top=g.y,bottom=g.y+g.h;
        if(projectileCrossesY(previousY,nextY,top,bottom)){
          const impactY=clamp((Math.max(low,top)+Math.min(high,bottom))/2,low,high),x=projectileXAt(b,impactY,previousY,nextY,previousX,nextX);
          if(x>=g.x&&x<=g.x+g.w)return {target:e,x,y:impactY};
        }
      }else if(e.type==="barrel"&&!e.resolved){
        const g=barrelGeometry(e),top=g.y,bottom=g.y+g.h;
        if(projectileCrossesY(previousY,nextY,top,bottom)){
          const impactY=clamp((Math.max(low,top)+Math.min(high,bottom))/2,low,high),x=projectileXAt(b,impactY,previousY,nextY,previousX,nextX);
          if(x>=g.x&&x<=g.x+g.w)return {target:e,x,y:impactY};
        }
      }else if(e.type==="boss"&&e.engaged&&e.hp>0){
        const road=roadAt(e.y),cx=road.left+road.width/2,scale=1.08+road.t*.16,top=e.y-55*scale,bottom=e.y+43*scale;
        if(projectileCrossesY(previousY,nextY,top,bottom)){
          const impactY=clamp((Math.max(low,top)+Math.min(high,bottom))/2,low,high),x=projectileXAt(b,impactY,previousY,nextY,previousX,nextX);
          if(Math.abs(x-cx)<=46*scale)return {target:e,x,y:impactY};
        }
      }
    }
    return null;
  }
  function findSquadProjectileHit(b,previousY,nextY,previousX,nextX) {
    const formation=squadFormation(),low=Math.min(previousY,nextY),high=Math.max(previousY,nextY),scale=formation.soldierScale;
    for(let i=0;i<formation.count;i++){
      const soldier=squadSoldierPosition(formation,i),top=soldier.y-21*scale,bottom=soldier.y+7*scale;
      if(!projectileCrossesY(previousY,nextY,top,bottom))continue;
      const impactY=clamp((Math.max(low,top)+Math.min(high,bottom))/2,low,high),x=projectileXAt(b,impactY,previousY,nextY,previousX,nextX);
      if(Math.abs(x-soldier.x)<=8*scale)return {x:soldier.x,y:impactY};
    }
    return null;
  }
  function applyEnemyProjectileHit(hit) {
    if(mode!=="running"||soldiers<=0)return;
    soldiers=Math.max(0,soldiers-1);
    const total=Number(canvas.dataset.enemyProjectileHits||0)+1;
    canvas.dataset.enemyProjectileHits=String(total);
    burst(hit.x,hit.y,C.red,5);
    say("Enemy round hit the squad · 1 unit lost");
    if(soldiers<=0)finishRun("lost");
  }
  function updatePlayerFire(dt) {
    if(mode!=="running")return;
    const engagedBoss=events.filter(e=>e.type==="boss"&&e.engaged).sort((a,b)=>b.y-a.y)[0]||null;
    const visibleEnemies=events
      .filter(e=>e.type==="enemy"&&e.count>0&&e.y>66&&e.y<PLAYER_Y+80)
      .sort((a,b)=>b.y-a.y);
    const playerSelectedTarget=activeSelectedTarget();
    const firstContactTarget=visibleEnemies.find(enemy=>!enemy.hasBeenHit)||null;
    const weights=laneFireWeights(lane);
    let fixedTarget=playerSelectedTarget||engagedBoss||firstContactTarget;
    if(!fixedTarget&&visibleEnemies.length===0){
      fixedTarget=events.filter(e=>(e.type==="target"||e.type==="barrel")&&isTargetSelectable(e))
        .sort((a,b)=>b.y-a.y)[0]||null;
    }
    if(playerSelectedTarget){
      canvas.dataset.combatLaneAligned="locked";
      canvas.dataset.combatTargetLane=String(playerSelectedTarget.type==="enemy"?playerSelectedTarget.lane:.5);
      canvas.dataset.combatTargetLaneShare="1";
      lastCombatTargetId=playerSelectedTarget.id;lastCombatAlignment="locked";
    }else if(engagedBoss){
      canvas.dataset.combatLaneAligned="true";
      canvas.dataset.combatTargetLane=String(lane);
      lastCombatTargetId=engagedBoss.id;
      lastCombatAlignment=true;
    }else if(visibleEnemies.length){
      const targetEnemy=visibleEnemies[0];
      const targetIndex=nearestLaneIndex(targetEnemy.lane);
      const targetShare=weights[targetIndex];
      const aligned=targetShare>0.001;
      canvas.dataset.combatLaneAligned=String(aligned);
      canvas.dataset.combatTargetLane=String(targetEnemy.lane);
      canvas.dataset.combatTargetLaneShare=targetShare.toFixed(3);
      if(targetEnemy.id!==lastCombatTargetId||aligned!==lastCombatAlignment){
        if(aligned) say("Sweeping fire into lane "+(targetIndex+1)+" ("+Math.round(targetShare*100)+"% of the volley).");
        else say("Enemy ahead in lane "+(targetIndex+1)+" — steer toward it to shift the firing spread.");
      }
      lastCombatTargetId=targetEnemy.id;
      lastCombatAlignment=aligned;
    }else{
      canvas.dataset.combatLaneAligned="none";
      canvas.dataset.combatTargetLane="";
      canvas.dataset.combatTargetLaneShare="0";
      lastCombatTargetId=null;
      lastCombatAlignment=null;
    }
    fireClock+=dt;
    const interval=testMode?0.18:0.3;
    while(fireClock>=interval){fireClock-=interval;fireVolley(fixedTarget);}
  }
  function applyProjectileHit(target) {
    if(selectedTargetId!==null&&target.id===selectedTargetId){
      totalSelectedTargetHits++;canvas.dataset.selectedTargetHits=String(totalSelectedTargetHits);
    }
    if(target.type==="enemy"){
      if(!events.includes(target)||target.count<=0)return;
      if(!target.engaged){
        totalEnemyHitsBeforeEngagement++;
        canvas.dataset.enemyHitsBeforeEngagement=String(totalEnemyHitsBeforeEngagement);
        if(!canvas.dataset.earlyEnemyHitY)canvas.dataset.earlyEnemyHitY=String(target.y);
        if(!canvas.dataset.firstEnemyHitSeconds)canvas.dataset.firstEnemyHitSeconds=simulationSeconds.toFixed(3);
      }
      target.hasBeenHit=true;
      target.count=Math.max(0,target.count-(tankTimeRemaining>0?TANK_DAMAGE:1));
      target.hitFlash=.14;
      totalEnemyHits++;
      canvas.dataset.enemyHits=String(totalEnemyHits);
    }else if(target.type==="boss"){
      if(!target.engaged||target.hp<=0)return;
      target.hp=Math.max(0,target.hp-(tankTimeRemaining>0?TANK_DAMAGE:1));
      target.hitFlash=.14;
      totalBossHits++;
      canvas.dataset.bossHits=String(totalBossHits);
    }else if(target.type==="barrel"){
      if(!events.includes(target)||target.resolved)return;
      target.hits=Math.min(target.hitsRequired||TANK_BARREL_HITS,(target.hits||0)+1);
      target.hitFlash=.12;lastTankBarrelHits=target.hits;
      canvas.dataset.tankBarrelHits=String(target.hits);
      if(target.hits>=(target.hitsRequired||TANK_BARREL_HITS))resolveBarrel(target);
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
    for(let i=bullets.length-1;i>=0;i--){
      const b=bullets[i],previousY=b.y,previousX=b.x;
      b.y+=b.vy*dt;
      if(b.roadLane!==undefined){
        if((b.team!=="enemy"&&b.y<=66)||(b.team==="enemy"&&b.y>=PLAYER_Y+35)){bullets.splice(i,1);continue;}
        b.x=roadXAtLane(b.y,b.roadLane);
        b.vx=dt>0?(b.x-previousX)/dt:0;
      }else{b.x+=b.vx*dt;}
      b.life-=dt;
      if(b.y>=66&&b.y<=H){
        const road=roadAt(b.y),margin=Math.min(9,road.width*.045);
        roadChecks++;
        if(b.x<road.left+margin||b.x>road.right-margin){roadViolations++;bullets.splice(i,1);continue;}
      }
      if(b.team==="enemy"){
        const hit=findSquadProjectileHit(b,previousY,b.y,previousX,b.x);
        if(hit){applyEnemyProjectileHit(hit);bullets.splice(i,1);continue;}
      }else{
        const hit=findPlayerProjectileHit(b,previousY,b.y,previousX,b.x);
        if(hit){
          applyProjectileHit(hit.target);
          burst(hit.x,hit.y,hit.target.type==="target"?C.lime:C.red,hit.target.type==="target"?7:5);
          bullets.splice(i,1);continue;
        }
      }
      if(b.life<=0||b.y<66||b.y>PLAYER_Y+35||b.x< -30||b.x>W+30)bullets.splice(i,1);
    }
    canvas.dataset.enemyProjectiles=String(bullets.filter(b=>b.team==="enemy").length);
    canvas.dataset.roadChecks=String(roadChecks);
    canvas.dataset.roadViolations=String(roadViolations);
  }
  function drawBullets() {
    canvas.dataset.projectiles=String(bullets.length);
    canvas.dataset.straightProjectiles=String(bullets.filter(b=>b.team==="player"&&b.straight===true&&b.targetId==null).length);
    canvas.dataset.playerBulletsStraight=String(bullets.filter(b=>b.team==="player").every(b=>b.straight===true&&b.targetId==null));
    ctx.save();
    bullets.forEach(b=>{
      const enemy=b.team==="enemy";
      ctx.save();ctx.translate(b.x,b.y);ctx.rotate(Math.atan2(b.vy,b.vx));
      ctx.strokeStyle=enemy?"rgba(255,89,103,.98)":"rgba(255,218,94,.98)";ctx.lineWidth=enemy?2.7:2.3;ctx.lineCap="round";
      ctx.shadowColor=enemy?"#ff4354":"#ffc83d";ctx.shadowBlur=6;
      ctx.beginPath();ctx.moveTo(-11,0);ctx.lineTo(-2,0);ctx.stroke();ctx.shadowBlur=0;
      ctx.fillStyle=enemy?"#ffd0d4":"#fff8ce";ctx.beginPath();ctx.ellipse(1,0,2.8,1.45,0,0,Math.PI*2);ctx.fill();
      ctx.restore();
    });
    ctx.restore();
  }
  function drawMuzzleFlashes() {
    ctx.save();ctx.globalCompositeOperation="lighter";
    muzzleFlashes.forEach(f=>{
      const alpha=clamp(f.life/f.max,0,1);
      ctx.save();ctx.globalAlpha=alpha;ctx.translate(f.x,f.y);
      const enemy=f.team==="enemy";
      ctx.fillStyle=enemy?"#ff8b96":"#fff7bd";ctx.beginPath();ctx.moveTo(0,-7);ctx.lineTo(2.3,-1.5);ctx.lineTo(6,0);ctx.lineTo(1.7,1.7);ctx.lineTo(0,6);ctx.lineTo(-1.5,1.8);ctx.lineTo(-5,0);ctx.lineTo(-1.8,-1.7);ctx.closePath();ctx.fill();
      ctx.strokeStyle=enemy?"rgba(255,83,98,.95)":"rgba(255,210,75,.95)";ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(-4,0);ctx.lineTo(4,0);ctx.moveTo(0,3);ctx.lineTo(0,-5);ctx.stroke();
      ctx.restore();
    });
    ctx.restore();
  }
  function drawParticles() {
    particles.forEach(p=>{ctx.globalAlpha=clamp(p.life/p.max,0,1);ctx.fillStyle=p.color;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();});ctx.globalAlpha=1;
  }
  function syncInteractionMetrics() {
    const target=activeSelectedTarget();
    canvas.dataset.selectedTargetId=target?String(target.id):"";
    canvas.dataset.selectedTargetType=target?target.type:"";
    canvas.dataset.selectedTargetHits=String(totalSelectedTargetHits);
    canvas.dataset.tankBarrelHits=String(lastTankBarrelHits);
    canvas.dataset.tankBarrelHitsRequired=String(TANK_BARREL_HITS);
    canvas.dataset.tankMode=String(tankTimeRemaining>0);
    canvas.dataset.tankTimeRemaining=Math.max(0,tankTimeRemaining).toFixed(2);
    canvas.dataset.tankDamage=String(TANK_DAMAGE);
    canvas.dataset.enemyProjectileHits=String(canvas.dataset.enemyProjectileHits||"0");
    canvas.dataset.enemyProjectiles=String(bullets.filter(b=>b.team==="enemy").length);
    canvas.dataset.straightProjectiles=String(bullets.filter(b=>b.team==="player"&&b.straight===true&&b.targetId==null).length);
    canvas.dataset.playerBulletsStraight=String(bullets.filter(b=>b.team==="player").every(b=>b.straight===true&&b.targetId==null));
  }
  function frame(now) {
    const frameDt=lastFrame?Math.min((now-lastFrame)/1000,.05):0;lastFrame=now;
    const dt=frameDt*speedMultiplier;
    update(dt);drawBackground(dt);drawRoad();drawEvents();drawSquad();drawBullets();drawMuzzleFlashes();drawParticles();syncHud();syncInteractionMetrics();
    requestAnimationFrame(frame);
  }

  let pointerDown=false,pointerMoved=false,pointerStartX=0,pointerStartY=0;
  canvas.addEventListener("pointerdown",e=>{
    if(mode!=="running")return;
    pointerDown=true;pointerMoved=false;pointerStartX=e.clientX;pointerStartY=e.clientY;
    pointerToLane(e);if(canvas.setPointerCapture)canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove",e=>{
    if(!pointerDown)return;
    if(!pointerMoved&&Math.hypot(e.clientX-pointerStartX,e.clientY-pointerStartY)>=7)pointerMoved=true;
    if(pointerMoved)pointerToLane(e);
  });
  canvas.addEventListener("pointerup",e=>{
    if(!pointerDown)return;
    if(!pointerMoved){
      const target=targetAtPoint(e);
      if(target)selectTarget(target);
    }
    pointerDown=false;pointerMoved=false;
  });
  canvas.addEventListener("pointercancel",()=>{pointerDown=false;pointerMoved=false;});
  window.addEventListener("keydown",e=>{
    if(mode!=="running")return;
    if(e.key==="ArrowLeft"||e.key.toLowerCase()==="a"){
      e.preventDefault();
      const current=nearestLaneIndex(targetLane);
      targetLane=LANE_CENTERS[Math.max(0,current-1)];
    }else if(e.key==="ArrowRight"||e.key.toLowerCase()==="d"){
      e.preventDefault();
      const current=nearestLaneIndex(targetLane);
      targetLane=LANE_CENTERS[Math.min(LANE_COUNT-1,current+1)];
    }
  });
  ui.startButton.addEventListener("click",startRun);ui.replay.addEventListener("click",startRun);ui.reset.addEventListener("click",resetState);
  ui.speedButtons.forEach(button=>button.addEventListener("click",()=>setGameSpeed(button.dataset.speed)));
  ui.fullscreen.addEventListener("click",async()=>{try{if(!document.fullscreenElement)await ui.frame.requestFullscreen();else await document.exitFullscreen();}catch(_e){say("Fullscreen is not available in this browser.");}});
  document.addEventListener("fullscreenchange",()=>{ui.fullscreen.setAttribute("aria-label",document.fullscreenElement?"Exit fullscreen":"Enter fullscreen");ui.fullscreen.querySelector("span").textContent=document.fullscreenElement?"EXIT FULLSCREEN":"FULLSCREEN";});
  function resizeCanvasToViewport() {
    const nextWidth=Math.max(220,Math.round(H*window.innerWidth/Math.max(1,window.innerHeight)));
    if(nextWidth===W&&canvas.height===H)return;
    const scale=nextWidth/W;
    W=nextWidth;canvas.width=W;canvas.height=H;
    bullets.forEach(b=>{b.x*=scale;if(Number.isFinite(b.vx))b.vx*=scale;if(Number.isFinite(b.targetX))b.targetX*=scale;});
    particles.forEach(p=>{p.x*=scale;if(Number.isFinite(p.vx))p.vx*=scale;});
    muzzleFlashes.forEach(f=>{f.x*=scale;});
  }
  window.addEventListener("resize",resizeCanvasToViewport,{passive:true});
  resetState();requestAnimationFrame(frame);
})();
