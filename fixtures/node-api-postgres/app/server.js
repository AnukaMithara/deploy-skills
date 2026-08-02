const http = require("node:http");
const { Pool } = require("pg");

const port = Number.parseInt(process.env.PORT || "3000", 10);
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

const server = http.createServer(async (request, response) => {
  response.setHeader("content-type", "application/json");
  if (request.url === "/health") {
    try {
      await pool.query("SELECT 1");
      response.writeHead(200);
      response.end(JSON.stringify({ status: "ok", database: "reachable" }));
    } catch (error) {
      response.writeHead(503);
      response.end(JSON.stringify({ status: "error", database: "unreachable" }));
    }
    return;
  }
  response.writeHead(200);
  response.end(JSON.stringify({ service: "node-api-postgres" }));
});

server.listen(port, "0.0.0.0");

async function shutdown() {
  server.close(async () => {
    await pool.end();
    process.exit(0);
  });
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
