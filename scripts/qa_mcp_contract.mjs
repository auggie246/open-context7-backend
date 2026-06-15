import { spawn } from "node:child_process";
import { once } from "node:events";

const serverPath = "src/context7--upstash-context7-mcp-3.2.1/packages/mcp/dist/index.js";
const child = spawn(process.execPath, [serverPath], {
  env: { ...process.env, CONTEXT7_API_URL: "http://127.0.0.1:8000/api" },
  stdio: ["pipe", "pipe", "pipe"],
});

let stdout = Buffer.alloc(0);
const responses = new Map();

process.stdout.write(
  "SDK_STDIO_FRAMING: newline-delimited JSON from @modelcontextprotocol/sdk shared/stdio.js serializeMessage\n",
);

child.stdout.on("data", (chunk) => {
  stdout = Buffer.concat([stdout, chunk]);
  parseFrames();
});

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
});

function send(message) {
  const body = JSON.stringify(message);
  child.stdin.write(`${body}\n`);
  process.stdout.write(`REQUEST ${body}\n`);
}

function parseFrames() {
  while (true) {
    const lineEnd = stdout.indexOf("\n");
    if (lineEnd < 0) return;
    const body = stdout.subarray(0, lineEnd).toString("utf8").trim();
    stdout = stdout.subarray(lineEnd + 1);
    if (!body.startsWith("{")) {
      process.stdout.write(`${body}\n`);
      continue;
    }
    const message = JSON.parse(body);
    process.stdout.write(`RESPONSE ${body}\n`);
    if (message.id !== undefined) responses.set(message.id, message);
  }
}

async function waitFor(id) {
  for (let i = 0; i < 100; i += 1) {
    if (responses.has(id)) return responses.get(id);
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`timeout waiting for response ${id}`);
}

send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "open-context7-backend-qa", version: "0.1.0" },
  },
});
await waitFor(1);
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({
  jsonrpc: "2.0",
  id: 2,
  method: "tools/call",
  params: {
    name: "resolve-library-id",
    arguments: { libraryName: "platform", query: "helm valuesFrom" },
  },
});
const resolveResponse = await waitFor(2);
send({
  jsonrpc: "2.0",
  id: 3,
  method: "tools/call",
  params: {
    name: "query-docs",
    arguments: { libraryId: "/internal/platform", query: "valuesFrom" },
  },
});
const docsResponse = await waitFor(3);

child.stdin.end();
child.kill();
await once(child, "close");

const transcript = JSON.stringify({ resolveResponse, docsResponse });
if (!transcript.includes("/internal/platform")) throw new Error("missing platform library");
if (!transcript.includes("Available Libraries")) throw new Error("missing search text");
if (!transcript.includes("TITLE:")) throw new Error("missing docs title");
process.stdout.write("MCP QA APPROVED\ncleanup: MCP child closed\n");
