let currentData = null;

const statRepos = document.getElementById("stat-repos");
const statFiles = document.getElementById("stat-files");
const statFunctions = document.getElementById("stat-functions");
const statUpdated = document.getElementById("stat-updated");
const languageSelect = document.getElementById("language-select");
const topnInput = document.getElementById("topn-input");
const chartContainer = document.getElementById("chart-container");
const tableContainer = document.getElementById("table-container");

function connectWebSocket() {
  const ws = new WebSocket(`ws://${location.host}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    currentData = data;
    render(data);
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => ws.close();
}

async function loadInitialData() {
  try {
    const res = await fetch("/api/data");
    if (res.ok) {
      const data = await res.json();
      currentData = data;
      render(data);
    }
  } catch (err) {
    console.log("Sin datos iniciales todavía.");
  }
}

function render(data) {
  updateStats(data);

  const language = languageSelect.value;
  const topn = parseInt(topnInput.value);

  const words = data.words[language] || {};
  let entries = Object.entries(words).sort((a, b) => b[1] - a[1]);

  if (!topn) {
    showTable(entries);
  } else {
    entries = entries.slice(0, topn);
    showChart(entries);
  }
}

function updateStats(data) {
  const stats = data.stats || {};
  statRepos.textContent = (stats.total_repos || 0).toLocaleString();
  statFiles.textContent = (stats.total_files || 0).toLocaleString();
  statFunctions.textContent = (stats.total_functions || 0).toLocaleString();

  if (data.last_updated) {
    const date = new Date(data.last_updated);
    statUpdated.textContent = date.toLocaleTimeString();
  }
}

function showChart(entries) {
  chartContainer.classList.remove("hidden");
  tableContainer.classList.add("hidden");
  chartContainer.innerHTML = "";

  if (entries.length === 0) {
    chartContainer.innerHTML =
      "<p style='color:#64748b;padding:16px'>Sin datos todavía.</p>";
    return;
  }

  const margin = { top: 10, right: 80, bottom: 20, left: 100 };
  const rowHeight = 28;
  const width = chartContainer.clientWidth - margin.left - margin.right;
  const height = entries.length * rowHeight;

  const svg = d3
    .select("#chart-container")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3
    .scaleLinear()
    .domain([0, d3.max(entries, (d) => d[1])])
    .range([0, width]);

  const y = d3
    .scaleBand()
    .domain(entries.map((d) => d[0]))
    .range([0, height])
    .padding(0.2);

  svg
    .append("g")
    .attr("class", "axis")
    .call(d3.axisLeft(y).tickSize(0))
    .select(".domain")
    .remove();

  svg
    .selectAll(".bar")
    .data(entries)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", 0)
    .attr("y", (d) => y(d[0]))
    .attr("width", (d) => x(d[1]))
    .attr("height", y.bandwidth());

  svg
    .selectAll(".bar-value")
    .data(entries)
    .enter()
    .append("text")
    .attr("class", "bar-value")
    .attr("x", (d) => x(d[1]) + 6)
    .attr("y", (d) => y(d[0]) + y.bandwidth() / 2 + 4)
    .text((d) => d[1].toLocaleString());
}

function showTable(entries) {
  tableContainer.classList.remove("hidden");
  chartContainer.classList.add("hidden");
  tableContainer.innerHTML = "";

  if (entries.length === 0) {
    tableContainer.innerHTML =
      "<p style='color:#64748b;padding:16px'>Sin datos todavía.</p>";
    return;
  }

  const table = document.createElement("table");
  table.innerHTML = `
    <thead>
      <tr>
        <th class="rank">#</th>
        <th>Palabra</th>
        <th>Apariciones</th>
      </tr>
    </thead>
  `;

  const tbody = document.createElement("tbody");
  entries.forEach(([word, count], i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="rank">${i + 1}</td>
      <td>${word}</td>
      <td>${count.toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  tableContainer.appendChild(table);
}

languageSelect.addEventListener("change", () => {
  if (currentData) render(currentData);
});

topnInput.addEventListener("input", () => {
  if (currentData) render(currentData);
});

connectWebSocket();
loadInitialData();
