let chart, historyChart;
const API="http://127.0.0.1:5000";
if(typeof Chart!=="undefined"){
  Chart.defaults.color="#7d88a6";
  Chart.defaults.borderColor="rgba(120,170,255,.12)";
  Chart.defaults.font.family="'JetBrains Mono', monospace";
}
const historyData={labels:[],readiness:[],fusion:[]};
const HISTORY_MAX=40;
let lastStatus=null,lastCoupled=null,lastScenario=null,lastRecoveryStatus=null;
function animateNumber(id,to,decimals=0){
  const el=document.getElementById(id);
  const from=parseFloat(el.textContent)||0;
  if(Math.abs(to-from)<0.05){el.textContent=to.toFixed(decimals);return}
  const start=performance.now(),duration=500;
  function tick(now){
    const t=Math.min(1,(now-start)/duration);
    const eased=1-Math.pow(1-t,3);
    el.textContent=(from+(to-from)*eased).toFixed(decimals);
    if(t<1)requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
function logEvent(text,level="info"){
  const log=document.getElementById("missionLog");
  if(!log)return;
  const time=new Date().toLocaleTimeString();
  const entry=document.createElement("div");
  entry.className=`log-entry ${level}`;
  entry.innerHTML=`<span class="log-time">${time}</span><span class="log-text">${text}</span>`;
  log.appendChild(entry);
  log.scrollTop=log.scrollHeight;
  while(log.children.length>60)log.removeChild(log.firstChild);
}
function runBootSequence(){
  const overlay=document.getElementById("bootOverlay"),lines=document.getElementById("bootLines");
  const seq=["Initializing MineSense AI core...","Connecting to ESP32 telemetry stream...","Loading sensor fusion engine...","Loading coupled degradation engine...","Loading trained ML model...","Establishing dashboard link...","System ready."];
  lines.innerHTML="";
  seq.forEach((text,i)=>{
    const div=document.createElement("div");
    div.className="boot-line pending";
    div.textContent=text;
    div.style.animationDelay=`${i*0.28}s`;
    lines.appendChild(div);
    setTimeout(()=>{div.className="boot-line done"},i*280+260);
  });
  setTimeout(()=>overlay.classList.add("hidden"),seq.length*280+700);
}

const envMeta={temperature:["🌡️","Temperature","Thermal condition","°C"],dust:["🌫️","Dust","Airborne particulate load","units"],motion:["📳","Vibration","Vehicle motion / instability","normalized"],ldr:["💡","Illumination","Visibility context","0–1023"]};
const perceptionMeta={camera:{icon:"📷",name:"Camera",metrics:[["visibility","Visibility","%"],["object_confidence","Object confidence","%"],["blur","Blur","%"]]},lidar:{icon:"📡",name:"LiDAR",metrics:[["effective_range_m","Effective range","m"],["point_density","Point density","%"],["noise","Noise","%"],["object_confidence","Object confidence","%"]]},radar:{icon:"📶",name:"Radar",metrics:[["detection_confidence","Detection confidence","%"],["snr","SNR","%"],["target_continuity","Target continuity","%"],["false_detections","False detections","%"]]}};
function pct(x){return Math.round((Number(x)||0)*100)}
function clamp(x){return Math.max(0,Math.min(100,x))}
function bar(id,v){const e=document.getElementById(id);if(e)e.style.width=`${clamp(v)}%`}
function statusClass(v){return v>=75?"good":v>=50?"warn":"bad"}
function renderEnvironment(data){const grid=document.getElementById("environmentGrid");grid.innerHTML="";for(const [key,m] of Object.entries(envMeta)){const score=data.anomaly_scores[key]||0,health=100-pct(score),p=data.predictions[key]||{};const value=key==="temperature"?Number(data.reading[key]).toFixed(1):key==="motion"?Number(data.reading[key]).toFixed(2):Math.round(data.reading[key]);grid.insertAdjacentHTML("beforeend",`<article class="sensor-card"><div class="sensor-head"><span>${m[0]}</span><div><h3>${m[1]}</h3><small>${m[2]}</small></div></div><div class="sensor-value">${value}</div><div class="unit">${m[3]}</div><div class="health-row"><span>Health</span><strong>${health}%</strong></div><div class="progress"><div class="${statusClass(health)}" style="width:${health}%"></div></div><div class="trend">${p.trend||"STABLE"} • anomaly ${pct(score)}%</div></article>`)}}
function metricValue(key,v){if(key==="effective_range_m")return `${Number(v).toFixed(0)} m`;if(key==="false_detections")return `${Number(v).toFixed(0)}%`;return `${Math.round(Number(v))}%`}
function renderPerception(data){const grid=document.getElementById("perceptionGrid");grid.innerHTML="";for(const [key,m] of Object.entries(perceptionMeta)){const d=data.perception[key],health=100-pct(data.perception_fusion.degradation_scores[key]||0);let rows=m.metrics.map(x=>`<div class="metric"><span>${x[1]}</span><b>${metricValue(x[0],d[x[0]])}</b></div>`).join("");grid.insertAdjacentHTML("beforeend",`<article class="perception-card"><div class="p-head"><span>${m.icon}</span><div><h3>${m.name}</h3><small>SIMULATED</small></div><strong>${health}%</strong></div><div class="progress"><div class="${statusClass(health)}" style="width:${health}%"></div></div><div class="metric-grid">${rows}</div><div class="health-label ${statusClass(health)}">${health>=75?"HEALTHY":health>=50?"DEGRADED":"HIGH RISK"}</div></article>`)}}
function renderFusion(data){const f=data.perception_fusion;document.getElementById("fusionCenter").textContent=`${Math.round(f.fused_perception_confidence)}%`;document.getElementById("fusionLabel").textContent=f.status;document.getElementById("redundancyValue").textContent=f.redundancy;document.getElementById("redundancyDetail").textContent=f.redundancy==="AVAILABLE"?"Multiple reliable perception channels remain.":f.redundancy==="LIMITED"?"Only partial sensor redundancy remains.":"Perception coverage is insufficient.";document.getElementById("redundancyText").textContent=`Redundancy: ${f.redundancy}`;document.getElementById("fusionNodes").innerHTML=["camera","lidar","radar"].map(k=>{const h=100-pct(f.degradation_scores[k]);return `<div class="fusion-node"><span>${perceptionMeta[k].icon}</span><b>${perceptionMeta[k].name}</b><strong>${Math.round(h)}%</strong></div>`}).join("")}
function renderChart(data){if(typeof Chart==="undefined")return;const keys=Object.keys(envMeta),labels=keys.map(k=>envMeta[k][1]),cur=keys.map(k=>pct(data.predictions[k]?.current_degradation)),proj=keys.map(k=>pct(data.predictions[k]?.predicted_degradation));if(chart)chart.destroy();chart=new Chart(document.getElementById("predictionChart"),{type:"bar",data:{labels,datasets:[{label:"Current degradation",data:cur},{label:"Projected degradation",data:proj}]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,max:100}},plugins:{legend:{position:"bottom"}}}})}
function renderCoupling(data){const c=data.coupled_degradation;document.getElementById("coupledBadge").textContent=c.detected?`${c.level} COUPLED DEGRADATION`:"NO COUPLING DETECTED";document.getElementById("coupledScore").textContent=pct(c.score);document.getElementById("affectedSensors").innerHTML=(c.affected_sensors||[]).map(s=>`<span class="chip">${perceptionMeta[s]?.name||envMeta[s]?.[1]||s}</span>`).join("")||'<span class="chip muted">None</span>';document.getElementById("coupledExplanation").textContent=c.explanation||"No coupled degradation detected."}
function renderRecovery(data){const r=data.recovery||{};document.getElementById("recoveryStatus").textContent=r.status||"--";document.getElementById("recoveryRate").textContent=r.recovery_rate_percent_per_step!=null?`+${r.recovery_rate_percent_per_step}% / step`:"--";document.getElementById("recoveryTime").textContent=r.estimated_recovery_minutes!=null?`${r.estimated_recovery_minutes} min`:"--";document.getElementById("recoveryConfidence").textContent=r.confidence?`${r.confidence}%`:"--";document.getElementById("recoveryNote").textContent=data.scenario==="recovery"?"Recovery is being evaluated from the readiness trajectory.":"Select Recovery to activate recovery-time estimation."}
function renderDiagnostic(data){const c=data.coupled_degradation,f=data.perception_fusion,r=data.system_readiness;const affected=(c.affected_sensors||[]).map(s=>perceptionMeta[s]?.name||envMeta[s]?.[1]||s).join(", ")||"No major channels";document.getElementById("diagnosticText").innerHTML=`<div class="diagnostic-line"><b>Current state</b><span>${r.status}</span></div><div class="diagnostic-line"><b>Perception</b><span>${Math.round(f.fused_perception_confidence)}% • ${f.status}</span></div><div class="diagnostic-line"><b>Coupling</b><span>${c.detected?c.level+" • "+affected:"Not detected"}</span></div><div class="diagnostic-line"><b>Inference</b><span>${c.detected?"Multiple channels are degrading in the same observation period.":"No simultaneous multi-channel degradation detected."}</span></div>`}
function renderSource(data){const el=document.getElementById("sourceBadge");const src=data.data_sources?.environmental||"--";const isReal=src.toUpperCase().includes("REAL");el.textContent=`ENV SOURCE: ${src}`;el.className="source-tag"+(isReal?" real":"")}
function renderMl(data){const m=data.ml_insight||{};const tagEl=document.getElementById("mlModelTag");if(!m.available){tagEl.textContent="MODEL: NOT TRAINED";document.getElementById("mlClass").textContent="--";document.getElementById("mlConfidence").textContent="--";document.getElementById("mlAccuracy").textContent="--";document.getElementById("mlExplanation").textContent=m.explanation||"Run generate_dataset.py then train_model.py in backend/.";document.getElementById("mlFeatures").innerHTML="";return}
tagEl.textContent=`MODEL: ${m.model_name.replaceAll("_"," ").toUpperCase()}`;document.getElementById("mlClass").textContent=m.predicted_class;document.getElementById("mlConfidence").textContent=`${m.confidence}%`;document.getElementById("mlAccuracy").textContent=`${m.test_accuracy}%`;document.getElementById("mlExplanation").textContent=m.explanation;document.getElementById("mlFeatures").innerHTML=(m.top_features||[]).map(x=>`<span class="chip">${x.name.replaceAll("_"," ")} • ${Math.round(x.importance*100)}%</span>`).join("")}
function renderHistory(data){
  if(typeof Chart==="undefined")return;
  const r=data.system_readiness,f=data.perception_fusion;
  historyData.labels.push(new Date().toLocaleTimeString().split(" ")[0]);
  historyData.readiness.push(r.readiness_score);
  historyData.fusion.push(f.fused_perception_confidence);
  if(historyData.labels.length>HISTORY_MAX){historyData.labels.shift();historyData.readiness.shift();historyData.fusion.shift()}
  if(!historyChart){
    historyChart=new Chart(document.getElementById("historyChart"),{
      type:"line",
      data:{labels:historyData.labels,datasets:[
        {label:"Readiness",data:historyData.readiness,borderColor:"#2fe6ff",backgroundColor:"rgba(47,230,255,.12)",tension:.35,fill:true,pointRadius:0,borderWidth:2},
        {label:"Fused Perception",data:historyData.fusion,borderColor:"#a06bff",backgroundColor:"rgba(160,107,255,.10)",tension:.35,fill:true,pointRadius:0,borderWidth:2}
      ]},
      options:{responsive:true,maintainAspectRatio:false,animation:{duration:300},scales:{y:{min:0,max:100,grid:{color:"rgba(120,170,255,.08)"}},x:{grid:{display:false},ticks:{maxTicksLimit:6}}},plugins:{legend:{position:"bottom",labels:{boxWidth:10}}}}
    });
  }else{
    historyChart.update();
  }
}
function narrateChanges(data){
  const r=data.system_readiness,c=data.coupled_degradation,src=data.data_sources?.environmental||"";
  if(lastScenario!==null&&data.scenario!==lastScenario){
    logEvent(`Scenario changed to ${data.scenario.replaceAll("_"," ").toUpperCase()}`,"info");
  }
  if(lastStatus!==null&&r.status!==lastStatus){
    const level=r.status==="CRITICAL"?"critical":r.status==="DEGRADED"?"warn":r.status==="READY"?"good":"info";
    logEvent(`Vehicle readiness changed: ${lastStatus} → ${r.status}`,level);
  }
  if(lastCoupled!==null&&c.detected&&!lastCoupled){
    logEvent(`Coupled degradation detected (${c.level}) — affected: ${(c.affected_sensors||[]).join(", ")||"multiple channels"}`,"critical");
  }
  if(lastCoupled!==null&&!c.detected&&lastCoupled){
    logEvent("Coupled degradation cleared — channels operating independently.","good");
  }
  if(data.recovery&&lastRecoveryStatus!==null&&data.recovery.status!==lastRecoveryStatus&&data.recovery.status==="RECOVERING"){
    logEvent(`Recovery in progress — est. ${data.recovery.estimated_recovery_minutes ?? "--"} min to target readiness.`,"good");
  }
  lastStatus=r.status;lastCoupled=c.detected;lastScenario=data.scenario;lastRecoveryStatus=data.recovery?.status;
}
function updateAlertVisuals(data){
  const critical=data.system_readiness.status==="CRITICAL";
  document.querySelectorAll(".hero-card")[0]?.classList.toggle("alert-critical",critical);
  document.querySelector(".response-panel")?.classList.toggle("alert-critical",critical);
}
function update(data){const r=data.system_readiness, f=data.perception_fusion;animateNumber("readinessScore",Number(r.readiness_score),1);document.getElementById("readinessStatus").textContent=r.status;bar("readinessBar",r.readiness_score);animateNumber("fusionScore",Math.round(f.fused_perception_confidence));document.getElementById("fusionStatus").textContent=f.status;const times=Object.values(data.predictions||{}).map(x=>x.time_to_critical_steps).filter(x=>x!=null);const mins=times.length?Math.max(1,Math.min(...times)*0.5):null;document.getElementById("criticalTime").textContent=mins?mins.toFixed(1):"--";const risk=100-r.readiness_score;document.getElementById("riskStatus").textContent=risk>=60?"HIGH RISK":risk>=35?"MEDIUM RISK":"LOW RISK";document.getElementById("predictionText").textContent=times.length?"Temporal model projects worsening conditions.":"No immediate critical estimate.";document.getElementById("lastUpdated").textContent=`${data.scenario.replaceAll("_"," ").toUpperCase()} • ${new Date().toLocaleTimeString()}`;renderEnvironment(data);renderPerception(data);renderFusion(data);renderChart(data);renderHistory(data);renderCoupling(data);renderRecovery(data);renderDiagnostic(data);renderSource(data);renderMl(data);narrateChanges(data);updateAlertVisuals(data);let title="Continue monitoring",text="Conditions remain within the current operating envelope.",action="MONITOR";if(r.status==="CRITICAL"){title="Critical perception readiness";text="Vehicle sensing capability is below the prototype safety threshold. Restrict operation and inspect affected channels.";action="RESTRICT OPERATION"}else if(data.coupled_degradation?.detected){title="Coupled degradation detected";text="Multiple sensing channels are degrading together. Inspect environmental exposure and affected perception channels.";action=data.coupled_degradation.level==="HIGH"?"INSPECT NOW":"ATTENTION"}else if(risk>=40){title="Degradation risk elevated";text="The predictive layer indicates worsening sensor performance.";action="CHECK SENSORS"}document.getElementById("responseTitle").textContent=title;document.getElementById("responseText").textContent=text;document.getElementById("responseAction").textContent=action;document.getElementById("connectionError").classList.add("hidden")}
async function fetchData(){try{const res=await fetch(`${API}/api/data`,{cache:"no-store"});if(!res.ok)throw Error();update(await res.json())}catch(e){document.getElementById("connectionError").classList.remove("hidden")}}
async function changeScenario(s){try{const res=await fetch(`${API}/api/scenario/${s}`);if(!res.ok)throw Error();await fetchData()}catch(e){document.getElementById("connectionError").classList.remove("hidden")}}
document.getElementById("scenarioSelect").addEventListener("change",e=>changeScenario(e.target.value));

const GUIDED_DEMO_STEPS=[
  {scenario:"normal",label:"Normal operation — real ESP32 baseline",hold:8000},
  {scenario:"dust_buildup",label:"Dust buildup begins — perception confidence starts falling",hold:9000},
  {scenario:"vibration",label:"Vibration stress added on top",hold:8000},
  {scenario:"coupled",label:"Coupled degradation — multiple channels degrading together",hold:10000},
  {scenario:"recovery",label:"Recovery — readiness trajectory restored",hold:10000},
];
let guidedDemoRunning=false;
async function runGuidedDemo(){
  if(guidedDemoRunning)return;
  guidedDemoRunning=true;
  const btn=document.getElementById("guidedDemoBtn"),status=document.getElementById("guidedDemoStatus");
  btn.disabled=true;btn.style.opacity=.5;
  for(const step of GUIDED_DEMO_STEPS){
    status.textContent=`${step.label} …`;
    logEvent(`Guided demo: ${step.label}`,"info");
    document.getElementById("scenarioSelect").value=step.scenario;
    await changeScenario(step.scenario);
    await new Promise(r=>setTimeout(r,step.hold));
  }
  status.textContent="Guided demo complete.";
  logEvent("Guided demo complete.","good");
  btn.disabled=false;btn.style.opacity=1;
  guidedDemoRunning=false;
}
runBootSequence();
logEvent("MineSense AI dashboard started.","info");
document.getElementById("guidedDemoBtn").addEventListener("click",runGuidedDemo);

fetchData();setInterval(fetchData,1500);
