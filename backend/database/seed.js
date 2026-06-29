// seed.js — creates a single initial admin operator account.
//
//   node database/seed.js <username> <password>
//
// Run once after first deployment, then change the password via your own
// admin tooling (this repo doesn't ship a self-service password-reset
// flow — see routes/auth.js's comment on why there's no signup endpoint).

const bcrypt = require("bcryptjs");
const { db } = require("./db");

function main() {
  const [, , username, password] = process.argv;
  if (!username || !password) {
    console.error("Usage: node database/seed.js <username> <password>");
    process.exit(1);
  }

  const passwordHash = bcrypt.hashSync(password, 10);
  const insert = db.prepare(
    "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)"
  );

  try {
    insert.run(username, passwordHash, Date.now() / 1000);
    console.log(`Created admin user '${username}'.`);
  } catch (err) {
    if (String(err.message).includes("UNIQUE constraint")) {
      console.error(`User '${username}' already exists.`);
    } else {
      throw err;
    }
  }
}

main();
