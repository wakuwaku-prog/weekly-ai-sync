"""Send the latest weekly AI report (or a given file) as an HTML email.

Requires environment variables:
    SMTP_USER       e.g. epiphany_0421@qq.com
    SMTP_AUTH_CODE  QQ mail SMTP authorization code (NOT the login password)
    MAIL_TO         recipient address, default same as SMTP_USER
Optional:
    SMTP_HOST       default smtp.qq.com
    SMTP_PORT       default 465
    SMTP_FROM       default SMTP_USER

Usage:
    python scripts/send_email.py
    python scripts/send_email.py --file weekly/2026-09-07-ai-weekly.md
"""

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
WEEKLY_DIR = ROOT / "weekly"
LITERATURE_DIR = ROOT / "literature"


def latest_report_path() -> Path:
    files = sorted(
        WEEKLY_DIR.glob("*-ai-weekly.md"),
        # Prefer the LLM-enhanced auto digest for email; fall back to a hand-edited report.
        key=lambda p: (p.name.startswith("auto-"), p.name),
        reverse=True,
    )
    if not files:
        raise FileNotFoundError("No weekly report found in weekly/")
    return files[0]


def latest_literature_path() -> Path | None:
    if not LITERATURE_DIR.exists():
        return None
    files = sorted(LITERATURE_DIR.glob("*.md"), key=lambda p: p.name, reverse=True)
    return files[0] if files else None


def build_html(md_text: str, site_url: str) -> str:
    body = markdown.markdown(md_text, extensions=["extra", "sane_lists", "toc"])
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.8;color:#1f2430;background:#f4f6fb;margin:0;padding:24px;">
<div style="max-width:720px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:32px;box-shadow:0 4px 16px rgba(16,24,40,.06);">
<div style="border-radius:12px;padding:24px;margin-bottom:24px;background:linear-gradient(135deg,#4f46e5,#0ea5e9);color:#fff;">
<h1 style="margin:0 0 8px;font-size:24px;">AI 每周热点同步</h1>
<p style="margin:0;opacity:.9;">自动抓取摘要已生成，完整内容可访问网站。</p>
</div>
{body}
<p style="margin-top:32px;padding-top:16px;border-top:1px solid #e2e8f0;color:#667085;font-size:13px;">
完整周报：<a href="{site_url}" style="color:#4f46e5;">{site_url}</a><br>
本邮件由 GitHub Actions 自动发送。
</p>
</div>
</body>
</html>
"""


def send_email(md_text: str, subject: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_code = os.getenv("SMTP_AUTH_CODE", "")
    mail_to = os.getenv("MAIL_TO", smtp_user)
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_code:
        print("Missing SMTP_USER or SMTP_AUTH_CODE environment variables.", file=sys.stderr)
        sys.exit(2)

    site_url = os.getenv("SITE_URL", "https://wakuwaku-prog.github.io/weekly-ai-sync/")
    html = build_html(md_text, site_url)

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((str(Header("AI Weekly Sync", "utf-8")), smtp_from))
    msg["To"] = mail_to
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(md_text[:4000], "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
        server.login(smtp_user, smtp_code)
        server.sendmail(smtp_from, [mail_to], msg.as_string())

    print(f"Email sent to {mail_to} with subject: {subject}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=None, help="Path to the markdown report")
    parser.add_argument("--no-literature", action="store_true", help="Do not append the latest literature digest")
    args = parser.parse_args()

    path = args.file if args.file else latest_report_path()
    md_text = path.read_text(encoding="utf-8")
    title_match = next((line for line in md_text.splitlines() if line.startswith("# ")), None)
    title = title_match.lstrip("# ").strip() if title_match else f"AI Weekly {path.stem[:10]}"

    if not args.no_literature:
        lit_path = latest_literature_path()
        if lit_path is not None:
            lit_md = lit_path.read_text(encoding="utf-8")
            md_text += "\n\n---\n\n" + lit_md
            title = f"{title} ＋ 植物囊泡文献追踪"

    send_email(md_text, title)


if __name__ == "__main__":
    main()