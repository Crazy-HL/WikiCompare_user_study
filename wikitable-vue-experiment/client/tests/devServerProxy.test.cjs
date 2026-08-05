const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(path.join(__dirname, "..", "vue.config.js"), "utf8");

assert(
  /devServer\s*:\s*\{/.test(source),
  "Vue development server should define devServer options"
);
assert(
  source.includes("'/api'") || source.includes('"/api"'),
  "Vue development server should proxy /api requests to the Tornado backend"
);
assert(
  source.includes("http://127.0.0.1:8888") || source.includes("http://localhost:8888"),
  "The /api proxy should target the local Tornado backend on port 8888"
);
assert(
  source.includes("changeOrigin: true"),
  "The /api proxy should enable changeOrigin for local API requests"
);

console.log("devServerProxy tests passed");
