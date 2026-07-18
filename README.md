# Etimad Cyber Opportunities Agent

Monitors Saudi tenders and saves cybersecurity opportunities to Excel and CSV every Sunday–Thursday at 09:00 Riyadh time.

The classifier covers GRC, SOC, SIEM, MDR, penetration testing, red teaming, vulnerability management, DLP, DAM, WAF, API security, IAM/PAM, threat intelligence, awareness, NCA, SAMA, CST, NDMO, PDPL and related Arabic terms.

## Required setup

The Etimad public page currently presents JavaScript plus CAPTCHA/WAF to automated visitors, so direct scraping is unreliable. This project uses a configurable tender-data API and does not bypass Etimad security controls.

1. Obtain a tender API key (the default adapter uses Tenders Alerts).
2. In GitHub open **Settings > Secrets and variables > Actions**.
3. Add a repository secret named `TENDERS_API_KEY`.
4. Open **Actions > Daily Etimad Cyber Scan > Run workflow**.

Reports appear under `output/`. Missing fields remain empty and are never written as `undefined`.
