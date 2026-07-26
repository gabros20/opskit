#!/usr/bin/env node
// ops-ui — the human terminal UI for ops. Bare `ops-ui` launches the guided loop.
// (The `ops` dispatcher's `bin/ui/` shim execs this binary when a human runs `ops ui`.)
import { main } from "./app.js";
import { VERSION } from "./version.js";

// --version must work non-interactively (BEFORE the TTY guard): the engine's `ui` setup layer runs
// it headlessly to detect a stale binary.
if (process.argv.includes("--version") || process.argv.includes("-v")) {
  console.log(VERSION);
  process.exit(0);
}

main()
  .then((code) => process.exit(code))
  .catch((e) => {
    console.error(e?.message ?? e);
    process.exit(1);
  });
