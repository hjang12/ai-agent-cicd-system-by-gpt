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

  const W = 960, H = 560, PLAYER_Y = 424, MAX_SOLDIERS = 120;
  const testMode = new URLSearchParams(location.search).get("testMode") === "1";
  const speed = testMode ? 520 : 136;
  const spawnInterval = testMode ? .96 : 2.05;
  const C = { lime:"#d6fa68", cyan:"#63e5e5", red:"#ff777f", purple:"#b4a1ff" };
  const add = (n, label) => ({ kind:"add", amount:n, label });
  const pct = (n, label) => ({ kind:"pct", amount:n, label });
  const mult = (n, label) => ({ kind:"mult", amount:n, label });
  const gate = (left, right, index) => ({ type:"gate", left, right, index });

  const ROUND = [
    gate(add(8,"+8"), pct(.5,"+50%"), 1),
    gate(mult(2,"×2"), add(12,"+12"), 2),
    gate(pct(.2,"+20%"), add(-4,"−4"), 3),
    { type:"enemy", count:18, lane:.49, label:"SCOUT SQUAD" },
    gate(add(10,"+10"), mult(2,"×2"), 4),
    gate(add(15,"+15"), pct(.5,"+50%"), 5),
    { type:"enemy", count:26, lane:.55, label:"ENEMY UNIT" },
    gate(mult(2,"×2"), pct(-.25,"−25%"), 6),
    { type:"enemy", count:32, lane:.46, label:"HEAVY UNIT" },
    gate(add(12,"+12"), pct(.4,"+40%"), 7),
    gate(mult(2,"×2"), add(18,"+18"), 8),
    { type:"boss", hp:76, label:"FINAL COMMANDER" }
  ];

  let mode="ready", soldiers=12, resolved=0, nextIndex=0, events=[];
  let spawnClock=0, fireClock=0, attackClock=0, lane=.5, targetLane=.5, offset=0, lastFrame=0;
  let message="Choose your route. The squad is waiting.", bullets=[], particles=[];
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
    if(mode==="ready") ui.enemy.textContent="GATES AHEAD";
    else if(mode==="won") ui.enemy.textContent="CLEARED";
    else if(mode==="lost") ui.enemy.textContent="SQUAD LOST";
    else if(events.some(e=>e.type==="boss"&&e.engaged)) ui.enemy.textContent="COMMANDER";
    else { const e=events.find(e=>e.type==="enemy"); ui.enemy.textContent=e?e.count+" ENEMIES":"GATES AHEAD"; }
  }
  function resetState() {
    mode="ready"; soldiers=12; resolved=0; nextIndex=0; events=[];
    spawnClock=0; fireClock=0; attackClock=0; lane=.5; targetLane=.5; bullets=[]; particles=[];
    ui.start.hidden=false; ui.end.hidden=true;
    say("Choose your route. The squad is waiting."); syncHud();
  }
  function startRun() {
    mode="running"; soldiers=12; resolved=0; nextIndex=1;
    events=[{...ROUND[0],id:0,y:84,engaged:false,resolved:false}];
    spawnClock=0; fireClock=0; attackClock=0; lane=.5; targetLane=.5; bullets=[]; particles=[];
    ui.start.hidden=true; ui.end.hidden=true;
    say("Run started. Pick the stronger gate."); syncHud();
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
    events.push({...ROUND[nextIndex],id:nextIndex,y:74,engaged:false,resolved:false});
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
    const sky=ctx.createLinearGradient(0,0,0,H);
    sky.addColorStop(0,"#10253a");sky.addColorStop(.46,"#1c4054");sky.addColorStop(1,"#0c2028");
    ctx.fillStyle=sky;ctx.fillRect(0,0,W,H);
    const glow=ctx.createRadialGradient(W/2,140,10,W/2,140,300);
    glow.addColorStop(0,"rgba(99,229,229,.2)");glow.addColorStop(1,"rgba(99,229,229,0)");
    ctx.fillStyle=glow;ctx.fillRect(100,0,W-200,330);
    ctx.fillStyle="#143044";ctx.beginPath();ctx.moveTo(0,190);
    [[100,110],[195,176],[285,96],[383,185],[483,122],[584,186],[700,108],[797,180],[883,112],[W,165]].forEach(p=>ctx.lineTo(p[0],p[1]));
    ctx.lineTo(W,265);ctx.lineTo(0,265);ctx.closePath();ctx.fill();
    ctx.fillStyle="#102a3b";
    for(let i=0;i<24;i++){const x=i*43-8,h=18+(i*19%39);ctx.fillRect(x,204-h,25,h+58);ctx.fillRect(x+29,211-h*.62,8,h*.62+50);}
    const ground=ctx.createLinearGradient(0,220,0,H);ground.addColorStop(0,"#173a39");ground.addColorStop(1,"#071a20");
    ctx.fillStyle=ground;ctx.fillRect(0,220,W,H-220);
    offset=(offset+dt*(mode==="running"?speed*.65:22))%70;
    ctx.strokeStyle="rgba(155,216,164,.11)";ctx.lineWidth=1;
    for(let y=228;y<H;y+=70){ctx.beginPath();ctx.moveTo(0,y+offset);ctx.lineTo(W,y+offset);ctx.stroke();}
  }
  function drawRoad() {
    const top=roadAt(66), bottom=roadAt(H), grad=ctx.createLinearGradient(0,100,0,H);
    grad.addColorStop(0,"#24384a");grad.addColorStop(1,"#111e2b");
    ctx.beginPath();ctx.moveTo(top.left,66);ctx.lineTo(top.right,66);ctx.lineTo(bottom.right,H);ctx.lineTo(bottom.left,H);ctx.closePath();ctx.fillStyle=grad;ctx.fill();
    ctx.lineWidth=3;ctx.strokeStyle="rgba(99,229,229,.7)";ctx.shadowColor="rgba(99,229,229,.55)";ctx.shadowBlur=12;
    ctx.beginPath();ctx.moveTo(top.left,66);ctx.lineTo(bottom.left,H);ctx.stroke();
    ctx.beginPath();ctx.moveTo(top.right,66);ctx.lineTo(bottom.right,H);ctx.stroke();ctx.shadowBlur=0;
    for(const f of [.333,.666]) {
      ctx.strokeStyle="rgba(184,211,225,.23)";ctx.lineWidth=2;ctx.setLineDash([17,16]);ctx.lineDashOffset=-offset*1.8;
      ctx.beginPath();ctx.moveTo(lerp(top.left,top.right,f),66);ctx.lineTo(lerp(bottom.left,bottom.right,f),H);ctx.stroke();ctx.setLineDash([]);
    }
    ctx.strokeStyle="rgba(214,250,104,.16)";ctx.lineWidth=1;
    for(let y=125;y<H;y+=63){const r=roadAt(y+offset);ctx.beginPath();ctx.moveTo(r.left+8,y+offset);ctx.lineTo(r.right-8,y+offset);ctx.stroke();}
  }
  function drawTrooper(x,y,s,enemy) {
    ctx.save();ctx.translate(x,y);ctx.scale(s,s);
    ctx.fillStyle="rgba(0,0,0,.34)";ctx.beginPath();ctx.ellipse(0,6,8,4,0,0,Math.PI*2);ctx.fill();
    roundRect(-5.4,-7,10.8,12,2.6,enemy?"#8d434d":"#799b4f",enemy?"#572c39":"#405b42");
    ctx.fillStyle=enemy?"#f2c4b1":"#f2d6ad";ctx.beginPath();ctx.arc(0,-9,4.4,0,Math.PI*2);ctx.fill();
    ctx.fillStyle=enemy?"#dd7279":"#c9e879";ctx.beginPath();ctx.arc(0,-11,4.8,Math.PI,Math.PI*2);ctx.lineTo(4.8,-9.5);ctx.lineTo(-4.8,-9.5);ctx.closePath();ctx.fill();
    ctx.strokeStyle=enemy?"#ffb5ac":"#d9fa8a";ctx.lineWidth=2.1;ctx.lineCap="round";
    ctx.beginPath();ctx.moveTo(-3,2);ctx.lineTo(-5,6);ctx.moveTo(3,2);ctx.lineTo(5,6);ctx.stroke();
    ctx.strokeStyle="#202b37";ctx.lineWidth=2.5;ctx.beginPath();ctx.moveTo(5,-4);ctx.lineTo(11,-7);ctx.stroke();ctx.restore();
  }
  function drawSquad() {
    const road=roadAt(PLAYER_Y), x=road.left+road.width*lane;
    ctx.fillStyle="rgba(99,229,229,.07)";ctx.beginPath();ctx.ellipse(x,PLAYER_Y+20,85,28,0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle="rgba(99,229,229,.21)";ctx.beginPath();ctx.ellipse(x,PLAYER_Y+20,85,28,0,0,Math.PI*2);ctx.stroke();
    const count=Math.min(soldiers,35);let row=0,start=0;
    for(let i=0;i<count;i++) {
      while(i>=start+(row*2+1)){start+=row*2+1;row++;}
      const col=i-start, sx=x+(col-row)*13, sy=PLAYER_Y-9+row*8.3;
      drawTrooper(sx,sy,.9-row*.025,false);
    }
    ctx.fillStyle="rgba(214,250,104,.94)";ctx.font="900 11px ui-sans-serif,system-ui";ctx.textAlign="center";ctx.fillText("YOUR SQUAD",x,PLAYER_Y+75);
  }
  function tint(effect) {
    if(effect.kind==="mult")return {c:C.cyan,bg:"rgba(99,229,229,.13)"};
    if(effect.kind==="pct")return effect.amount<0?{c:C.red,bg:"rgba(255,119,127,.13)"}:{c:C.purple,bg:"rgba(180,161,255,.13)"};
    if(effect.amount<0)return {c:C.red,bg:"rgba(255,119,127,.13)"};
    return {c:C.lime,bg:"rgba(214,250,104,.13)"};
  }
  function drawGatePanel(x,y,w,h,effect,s) {
    const t=tint(effect);ctx.save();ctx.shadowColor=t.c;ctx.shadowBlur=16*s;
    roundRect(x,y,w,h,6*s,t.bg,t.c);ctx.shadowBlur=0;ctx.strokeStyle=t.c;ctx.lineWidth=Math.max(1.2,2*s);
    ctx.beginPath();ctx.moveTo(x+4*s,y+h);ctx.lineTo(x+4*s,y-4*s);ctx.moveTo(x+w-4*s,y+h);ctx.lineTo(x+w-4*s,y-4*s);ctx.stroke();
    ctx.fillStyle=t.c;ctx.textAlign="center";ctx.textBaseline="middle";ctx.font="900 "+Math.round(23*s)+"px ui-sans-serif,system-ui";ctx.fillText(effect.label,x+w/2,y+h*.52);
    ctx.fillStyle="rgba(236,246,252,.74)";ctx.font="800 "+Math.max(7,Math.round(8*s))+"px ui-sans-serif,system-ui";ctx.fillText("SQUAD GATE",x+w/2,y-8*s);ctx.restore();
  }
  function drawGate(e) {
    const r=roadAt(e.y),s=.42+r.t*.72,h=21+r.t*37,y=e.y-h,gap=5*s,half=r.width/2;
    drawGatePanel(r.left+4,y,half-7,h,e.left,s);drawGatePanel(r.left+half+gap,y,half-7,h,e.right,s);
    ctx.fillStyle="rgba(4,12,20,.7)";ctx.fillRect(r.left+half-2,y-2,4,h+5);
  }
  function drawEnemy(e) {
    const r=roadAt(e.y),x=r.left+r.width*e.lane,s=.48+r.t*.66;
    ctx.fillStyle="rgba(255,119,127,.12)";ctx.beginPath();ctx.ellipse(x,e.y+12,62*s,18*s,0,0,Math.PI*2);ctx.fill();
    const n=Math.min(13,Math.max(6,Math.round(e.count/2.8)));
    for(let i=0;i<n;i++){const row=Math.floor(i/5),col=i%5;drawTrooper(x+(col-2)*15*s,e.y+row*10*s,s*.83,true);}
    ctx.fillStyle="#ffc3bf";ctx.textAlign="center";ctx.font="900 "+Math.max(8,Math.round(10*s))+"px ui-sans-serif,system-ui";ctx.fillText("ENEMY "+e.count,x,e.y-22*s);
  }
  function drawBoss(e) {
    const r=roadAt(e.y),x=r.left+r.width/2,s=1.02+r.t*.12;
    const glow=ctx.createRadialGradient(x,e.y,8,x,e.y,105);glow.addColorStop(0,"rgba(255,119,127,.25)");glow.addColorStop(1,"rgba(255,119,127,0)");
    ctx.fillStyle=glow;ctx.fillRect(x-120,e.y-125,240,220);ctx.save();ctx.translate(x,e.y);ctx.scale(s,s);
    ctx.fillStyle="rgba(0,0,0,.42)";ctx.beginPath();ctx.ellipse(0,37,36,12,0,0,Math.PI*2);ctx.fill();
    roundRect(-28,-16,56,50,8,"#6b3945","#ff8a8f");roundRect(-36,-6,13,29,4,"#8c4c55","#e37d7f");roundRect(23,-6,13,29,4,"#8c4c55","#e37d7f");
    ctx.fillStyle="#f7c8a4";ctx.beginPath();ctx.arc(0,-29,21,0,Math.PI*2);ctx.fill();
    ctx.fillStyle="#d86e75";ctx.beginPath();ctx.moveTo(-24,-30);ctx.lineTo(-15,-48);ctx.lineTo(-2,-41);ctx.lineTo(13,-49);ctx.lineTo(24,-30);ctx.lineTo(19,-20);ctx.lineTo(-19,-20);ctx.closePath();ctx.fill();
    roundRect(-15,-30,30,8,3,"#202b39","#ffb1a7");ctx.fillStyle=C.red;ctx.fillRect(-5,-28,10,3);ctx.restore();
    ctx.textAlign="center";ctx.fillStyle="#ffb4b4";ctx.font="900 11px ui-sans-serif,system-ui";ctx.fillText("FINAL COMMANDER",x,e.y-71);
    const bw=126,by=e.y-60;roundRect(x-bw/2,by,bw,7,3,"rgba(8,13,22,.9)","rgba(255,119,127,.65)");
    if(e.hp>0)roundRect(x-bw/2+1,by+1,(bw-2)*clamp(e.hp/e.maxHp,0,1),5,2,C.red);
  }
  function drawEvents() {
    events.forEach(e=>{
      if(e.type==="gate"&&e.y>62&&e.y<H+60)drawGate(e);
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
      if(e.type==="boss"&&e.engaged){updateBoss(e,dt);continue;}
      e.y+=speed*dt;
      if(e.type==="gate"&&e.y>=PLAYER_Y-24){resolveGate(e);events.splice(i,1);continue;}
      if(e.type==="enemy"&&e.y>=PLAYER_Y-18){resolveEnemy(e);events.splice(i,1);if(mode!=="running")return;continue;}
      if(e.type==="boss"&&e.y>=PLAYER_Y-124){e.engaged=true;e.y=PLAYER_Y-119;e.maxHp=e.hp;attackClock=0;say("Final commander engaged. Auto-fire on target.");}
    }
    updatePlayerFire(dt);
    updateBullets(dt);
    if(mode==="running"&&nextIndex>=ROUND.length&&events.length===0)finishRun("won");
  }
  function updateBoss(e,dt) {
    attackClock+=dt;
    e.hp-=soldiers*.35*dt;
    if(soldiers<24&&attackClock>.8){attackClock=0;soldiers=Math.max(0,soldiers-2);say("Commander counterattack  ·  2 units lost");burst(px,PLAYER_Y-10,C.red,6);if(soldiers<=0){finishRun("lost");return;}}
    if(e.hp<=0){resolved++;events=events.filter(item=>item!==e);finishRun("won");}
  }
  function projectileTargetPoint(target) {
    const road=roadAt(target.y);
    if(target.type==="boss") return {x:road.left+road.width/2,y:target.y-27};
    return {x:road.left+road.width*target.lane,y:target.y};
  }
  function fireVolley(target) {
    const fromRoad=roadAt(PLAYER_Y),fromX=fromRoad.left+fromRoad.width*lane;
    const aim=projectileTargetPoint(target);
    [-15,0,15].forEach(spread=>{
      const x=fromX+spread,y=PLAYER_Y-12,dx=aim.x-x,dy=aim.y-y,dist=Math.hypot(dx,dy)||1;
      const velocity= testMode ? 980 : 760;
      bullets.push({
        x,y,vx:dx/dist*velocity,vy:dy/dist*velocity,life:2.4,
        targetId:target.id,targetX:aim.x,targetY:aim.y
      });
    });
  }
  function updatePlayerFire(dt) {
    if(mode!=="running") return;
    const target=events.find(e=>e.type==="boss"&&e.engaged)
      || events.filter(e=>e.type==="enemy"&&e.y<PLAYER_Y+8).sort((a,b)=>b.y-a.y)[0];
    if(!target){fireClock=0;return;}
    fireClock+=dt;
    const interval=testMode ? 0.18 : 0.3;
    while(fireClock>=interval){fireClock-=interval;fireVolley(target);}
  }
  function updateBullets(dt) {
    const velocity=testMode?980:760;
    for(let i=bullets.length-1;i>=0;i--){
      const b=bullets[i],target=events.find(e=>e.id===b.targetId);
      const aim=target?projectileTargetPoint(target):{x:b.targetX,y:b.targetY};
      const dx=aim.x-b.x,dy=aim.y-b.y,dist=Math.hypot(dx,dy)||1;
      if(dist<=Math.max(12,velocity*dt)){
        burst(aim.x,aim.y,target&&target.type==="boss"?C.cyan:C.red,3);
        bullets.splice(i,1);
        continue;
      }
      if(target){b.vx=dx/dist*velocity;b.vy=dy/dist*velocity;b.targetX=aim.x;b.targetY=aim.y;}
      b.x+=b.vx*dt;b.y+=b.vy*dt;b.life-=dt;
      if(b.life<=0||b.y<0||b.x< -30||b.x>W+30){bullets.splice(i,1);}
    }
  }
  function drawBullets() {
    canvas.dataset.projectiles=String(bullets.length);
    ctx.save();
    bullets.forEach(b=>{
      ctx.save();ctx.translate(b.x,b.y);ctx.rotate(Math.atan2(b.vy,b.vx));
      ctx.strokeStyle="rgba(99,229,229,.8)";ctx.lineWidth=2.5;ctx.lineCap="round";
      ctx.shadowColor=C.cyan;ctx.shadowBlur=8;
      ctx.beginPath();ctx.moveTo(-15,0);ctx.lineTo(-3,0);ctx.stroke();ctx.shadowBlur=0;
      ctx.fillStyle=C.lime;ctx.beginPath();ctx.moveTo(8,0);ctx.lineTo(-3,-3.5);ctx.lineTo(-1,0);ctx.lineTo(-3,3.5);ctx.closePath();ctx.fill();
      ctx.fillStyle="#f2fff0";ctx.fillRect(-4,-1,7,2);
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
