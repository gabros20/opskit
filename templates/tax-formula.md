---
currency: HUF
vat_rate: 0.27
seller_name: Your Name / Company Kft.
seller_tax_id: 00000000-0-00
payment_terms_days: 15
---
# Tax formula

The single source of truth for how `plainkeep invoice` computes a draft. Edit these to your
jurisdiction. `plainkeep invoice` reads the frontmatter above:

- `vat_rate` — applied as `gross = net * (1 + vat_rate)`. (0.27 = Hungarian ÁFA.)
- `currency` — printed on the draft.
- `seller_*` — your details on the draft header.
- `payment_terms_days` — due date = invoice date + this many days.

`plainkeep invoice` only ever produces a DRAFT in the client's `~/files/.../out/` folder. It never
sends anything — you review and send by hand (§3).
