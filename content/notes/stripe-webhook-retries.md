---
type: note
title: Stripe webhook retries
status: evergreen
created: 2026-03-01
updated: 2026-06-10
tags: [stripe, webhooks]
---
# Stripe webhook retries
Stripe retries failed webhooks with [[exponential-backoff]] over up to 3 days.

## Configuration
Set the endpoint to return 2xx quickly; do heavy work async so retries don't pile up.
