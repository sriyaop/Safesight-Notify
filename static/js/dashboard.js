/* -------------------------------- */
/* GLOBAL ELEMENTS */
/* -------------------------------- */

const logTable = document.getElementById("logTable");

const detectedPeople = new Set();
const loggedPeople = new Set();

let activeAlerts = 0;
const activePopupNames = new Set();


/* -------------------------------- */
/* METRICS FETCH */
/* -------------------------------- */

function loadMetrics(){

fetch("/metrics")
.then(res=>res.json())
.then(data=>{

document.getElementById("missingCount").innerText =
data.missing_children;

});

}

loadMetrics();


/* -------------------------------- */
/* FACE MATCH ANALYSIS PER CAMERA */
/* -------------------------------- */

function renderFaceAnalysis(camera, results){

const container = document.getElementById("analysis_" + camera);

if(!container) return;

container.innerHTML = "";

results.forEach(result => {

const card = document.createElement("div");
card.className = "analysis-row";

/* detected camera face */

const camImg = document.createElement("img");
camImg.className = "analysis-face";
camImg.src = "data:image/jpeg;base64," + result.face;

/* database face */

const dbImg = document.createElement("img");
dbImg.className = "analysis-face";
dbImg.src = result.db_image;

/* info */

const info = document.createElement("div");
info.className = "analysis-info";

const label = document.createElement("div");
label.className = "analysis-label";
label.innerText = `${result.name} (${result.confidence}%)`;

const bar = document.createElement("div");
bar.className = "analysis-bar";

const fill = document.createElement("div");
fill.className = "analysis-fill";
fill.style.width = result.confidence + "%";

bar.appendChild(fill);

info.appendChild(label);
info.appendChild(bar);

card.appendChild(camImg);
card.appendChild(dbImg);
card.appendChild(info);

container.appendChild(card);

handleDetection(result);
showPopup(result);

});

}


/* -------------------------------- */
/* DETECTION HANDLING */
/* -------------------------------- */

function handleDetection(result){

const name=result.name;

if(!detectedPeople.has(name)){
detectedPeople.add(name);

document.getElementById("faceCount").innerText =
detectedPeople.size;
}

if(!loggedPeople.has(name)){
addLog(result);
loggedPeople.add(name);
}

}


function addLog(result){

const row=document.createElement("tr");

row.innerHTML=`
<td>${new Date().toLocaleTimeString()}</td>
<td>-</td>
<td>${result.name}</td>
<td>${result.confidence}%</td>
`;

logTable.prepend(row);

if(logTable.rows.length>30){
logTable.deleteRow(-1);
}

}


/* -------------------------------- */
/* ALERT POPUPS */
/* -------------------------------- */

function showPopup(result){

const name = result.name;

if(activePopupNames.has(name)) return;

activePopupNames.add(name);

const popup=document.createElement("div");
popup.className="alert-popup";

popup.innerText=`MATCH FOUND: ${result.name} (${result.confidence}%)`;

const offset = activeAlerts * 70;

popup.style.top = 30 + offset + "px";
popup.style.right = "30px";

document.body.appendChild(popup);

activeAlerts++;

document.getElementById("alertCount").innerText = activeAlerts;

setTimeout(()=>{

popup.remove();

activeAlerts--;

document.getElementById("alertCount").innerText = activeAlerts;

activePopupNames.delete(name);

},4000);

}


/* -------------------------------- */
/* FETCH CAMERA RESULTS */
/* -------------------------------- */

function fetchCameraResults(){

fetch("/camera_results")
.then(res=>res.json())
.then(data=>{

for(const camera in data){

const results = data[camera];

/* sort by confidence */

results.sort((a,b)=>b.confidence-a.confidence);

/* render analysis for that camera */

renderFaceAnalysis(camera, results);

}

});

}


/* -------------------------------- */
/* POLLING LOOP */
/* -------------------------------- */

setInterval(fetchCameraResults,2000);