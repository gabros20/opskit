// Render an ops --json result for a human. The envelope's error.hint / exit-3 re-run / exit-4
// did-you-mean ARE the UX ("refusals teach") — we surface them verbatim, never flatten to "failed".
import pc from "picocolors";
import type { RunResult } from "./ops.js";
import { EXIT } from "./ops.js";

export function renderResult(res: RunResult): void {
  const env = res.envelope;

  // Error / refusal envelope.
  if (env && env.ok === false && env.error) {
    const { code, message, hint } = env.error;
    const label =
      code === EXIT.CONFIRM ? pc.yellow("needs confirmation")
      : code === EXIT.NOT_FOUND ? pc.yellow("not found")
      : code === EXIT.DENY ? pc.red("denied")
      : code === EXIT.USAGE ? pc.yellow("usage")
      : pc.red("error");
    console.log(`  ${label}: ${message}`);
    if (hint) console.log(pc.dim(`  → ${hint}`));
    return;
  }

  // Rows (list verbs): print a compact table.
  if (res.rows.length > 0) {
    printRows(res.rows);
    if (env?.count != null) console.log(pc.dim(`  ${env.count} result${env.count === 1 ? "" : "s"}`));
    return;
  }

  // Scalar data.
  if (env?.data && Object.keys(env.data).length > 0) {
    for (const [k, v] of Object.entries(env.data)) {
      console.log(`  ${pc.dim(k)}: ${format(v)}`);
    }
    return;
  }

  // Fallback: raw stdout (e.g. a verb run without --json), else a bare ok.
  if (res.raw.trim()) console.log(res.raw.trimEnd());
  else if (env?.ok) console.log(pc.green("  ✓ done"));
}

function printRows(rows: Record<string, unknown>[]): void {
  const cols = [...new Set(rows.flatMap((r) => Object.keys(r)))].slice(0, 4);
  const widths = cols.map((c) => Math.max(c.length, ...rows.map((r) => String(r[c] ?? "").length)));
  const trunc = (s: string, w: number) => (s.length > w ? s.slice(0, w - 1) + "…" : s.padEnd(w));
  console.log("  " + pc.dim(cols.map((c, i) => trunc(c, Math.min(widths[i], 40))).join("  ")));
  for (const r of rows.slice(0, 50)) {
    console.log("  " + cols.map((c, i) => trunc(String(r[c] ?? ""), Math.min(widths[i], 40))).join("  "));
  }
  if (rows.length > 50) console.log(pc.dim(`  … and ${rows.length - 50} more`));
}

function format(v: unknown): string {
  if (v == null) return pc.dim("—");
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (Array.isArray(v)) return v.length ? v.map((x) => format(x)).join(", ") : pc.dim("(none)");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}
