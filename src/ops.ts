// The bridge to the ops engine. ops-ui NEVER imports ops internals — it shells to the same public
// `ops <verb> --json` surface an agent uses, so the guardrail + .logs see every action (one door).
import { execa } from "execa";
import { existsSync } from "node:fs";

// Locate the `ops` dispatcher: explicit $OPS_BIN wins (an absolute path to the ops script), else the
// `ops` on PATH. We resolve it once. The TUI is useless without it — fail loudly with the fix.
export function resolveOpsBin(): string {
  const explicit = process.env.OPS_BIN;
  if (explicit) {
    if (existsSync(explicit)) return explicit;
    throw new OpsMissing(`OPS_BIN=${explicit} does not exist`);
  }
  // Rely on PATH resolution via the shell — execa with a bare name searches PATH.
  return "ops";
}

export class OpsMissing extends Error {}

// The exit-code protocol (machine-contract §2): 0 ok · 2 usage · 3 confirm · 4 not-found · 5 deny.
export const EXIT = { OK: 0, USAGE: 2, CONFIRM: 3, NOT_FOUND: 4, DENY: 5 } as const;

export interface Envelope {
  ops_json: number;
  ok: boolean;
  verb: string;
  data?: Record<string, unknown>;
  error?: { code: number; message: string; hint?: string };
  count?: number; // rows header
}

export interface RunResult {
  exitCode: number;
  envelope: Envelope | null; // the scalar/header envelope
  rows: Record<string, unknown>[]; // NDJSON data rows (for list verbs), excluding the header
  raw: string; // stdout, for fallback rendering
  stderr: string;
}

// Run `ops <argv...> --json` and parse the envelope. Never throws on a non-zero ops exit — a refusal
// (exit 3/4/5) is normal control flow the UI renders; only a spawn failure (ops missing) throws.
export async function runOps(argv: string[], opts: { json?: boolean } = {}): Promise<RunResult> {
  const bin = resolveOpsBin();
  const args = opts.json === false ? argv : [...argv, "--json"];
  let stdout = "";
  let stderr = "";
  let exitCode = 0;
  try {
    const res = await execa(bin, args, { reject: false, all: false });
    stdout = res.stdout ?? "";
    stderr = res.stderr ?? "";
    exitCode = res.exitCode ?? 1;
  } catch (e: any) {
    if (e?.code === "ENOENT") {
      throw new OpsMissing(
        "the `ops` command was not found on PATH. Install/link the ops vault (script/setup puts it " +
          "on PATH), or set OPS_BIN=/absolute/path/to/ops.",
      );
    }
    throw e;
  }
  const { envelope, rows } = parseJsonl(stdout);
  return { exitCode, envelope, rows, raw: stdout, stderr };
}

// For tty-class verbs (backup init's password prompt, wiki edit → $EDITOR): hand the real terminal
// to ops — inherit stdio, no --json capture — and return the exit code. This is the "suspend and
// pass through" path the tty flag exists for.
export async function runOpsInteractive(argv: string[]): Promise<number> {
  const bin = resolveOpsBin();
  try {
    const res = await execa(bin, argv, { stdio: "inherit", reject: false });
    return res.exitCode ?? 1;
  } catch (e: any) {
    if (e?.code === "ENOENT") throw new OpsMissing("`ops` not found on PATH (set OPS_BIN).");
    throw e;
  }
}

// Parse the ops JSON output: either a single scalar envelope object, or NDJSON (one header envelope
// then one data row per line). Tolerant of blank lines and trailing noise.
function parseJsonl(text: string): { envelope: Envelope | null; rows: Record<string, unknown>[] } {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  let envelope: Envelope | null = null;
  const rows: Record<string, unknown>[] = [];
  for (const line of lines) {
    let obj: any;
    try {
      obj = JSON.parse(line);
    } catch {
      continue; // skip non-JSON noise
    }
    if (obj && typeof obj === "object" && "ops_json" in obj) {
      envelope = obj as Envelope; // the (last) header/scalar envelope
    } else if (obj && typeof obj === "object") {
      rows.push(obj as Record<string, unknown>);
    }
  }
  return { envelope, rows };
}
