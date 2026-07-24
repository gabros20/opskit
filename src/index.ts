#!/usr/bin/env node
// ops-ui — the human terminal UI for ops. Bare `ops-ui` launches the guided loop.
// (The `ops` dispatcher's `bin/ui/` shim execs this binary when a human runs `ops ui`.)
import { main } from "./app.js";

main()
  .then((code) => process.exit(code))
  .catch((e) => {
    console.error(e?.message ?? e);
    process.exit(1);
  });
