const { readFile } = require("node:fs/promises");
const { Client } = require("pg");

async function migrate() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();
  try {
    const sql = await readFile("migrations/001_create_deployment_probe.sql", "utf8");
    await client.query(sql);
  } finally {
    await client.end();
  }
}

migrate().catch((error) => {
  console.error("migration failed", error.message);
  process.exit(1);
});
