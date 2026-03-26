const http = require("http");
const path = require("path");
const express = require("express");
const { WebSocketServer } = require("ws");
const watcher = require("./watcher");
const EXTERNAL_PORT = process.env.EXTERNAL_PORT || PORT;

const PORT = parseInt(process.env.PORT || "8080");

const app = express();

app.use(express.static(path.join(__dirname, "public")));

app.get("/api/data", (req, res) => {
  if (watcher.lastUpdated === null) {
    return res.status(503).json({
      error: "Sin datos todavía, el miner aún no ha escrito resultados.",
    });
  }

  try {
    const fs = require("fs");
    const jsonPath =
      process.env.JSON_PATH || path.join(__dirname, "../../shared/words.json");
    const raw = fs.readFileSync(jsonPath, "utf-8");
    return res.json(JSON.parse(raw));
  } catch (err) {
    return res.status(500).json({ error: "Error leyendo words.json" });
  }
});

const server = http.createServer(app);

const wss = new WebSocketServer({ server });

wss.on("connection", (ws) => {
  console.log("Cliente conectado via WebSocket");

  ws.on("close", () => {
    console.log("Cliente desconectado");
  });
});

watcher.on("change", (data) => {
  const message = JSON.stringify(data);
  wss.clients.forEach((client) => {
    if (client.readyState === 1) {
      client.send(message);
    }
  });
});

watcher.start();

server.listen(PORT, () => {
  console.log(
    `Visualizer corriendo en local ${PORT} y visible en http://localhost:${EXTERNAL_PORT}`,
  );
});
