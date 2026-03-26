const fs = require("fs");
const path = require("path");
const EventEmitter = require("events");

const JSON_PATH =
  process.env.JSON_PATH || path.join(__dirname, "../../shared/words.json");
const POLL_INTERVAL_MS = parseInt(process.env.POLL_INTERVAL_MS || "2000");

class Watcher extends EventEmitter {
  constructor() {
    super();
    this.lastUpdated = null;
    this.interval = null;
  }

  start() {
    console.log(`Watching ${JSON_PATH} every ${POLL_INTERVAL_MS}ms`);
    this.interval = setInterval(() => this.check(), POLL_INTERVAL_MS);
    this.check();
  }

  check() {
    if (!fs.existsSync(JSON_PATH)) {
      return;
    }

    try {
      const raw = fs.readFileSync(JSON_PATH, "utf-8");
      const data = JSON.parse(raw);

      if (data.last_updated !== this.lastUpdated) {
        this.lastUpdated = data.last_updated;
        this.emit("change", data);
      }
    } catch (err) {}
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
}

module.exports = new Watcher();
