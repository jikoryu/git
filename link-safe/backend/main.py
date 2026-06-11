"""Link Safe — FastAPI entry point."""

import asyncio
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models import AnalyzeRequest, AnalysisReport
from analyzer import (
    check_url_validity,
    check_ssl,
    check_domain_age,
    check_blacklist,
    check_short_link,
    check_suspicious_keywords,
    compute_overall,
)

app = FastAPI(title="Link Safe", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/analyze", response_model=AnalysisReport)
async def analyze(data: AnalyzeRequest):
    """Run all 6 security checks on a URL."""
    url = data.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.hostname or ""

    if not domain:
        raise HTTPException(400, "无法解析 URL")

    # Run the 4 synchronous checks in a thread pool
    loop = asyncio.get_event_loop()
    url_check, ssl_check, age_check, bl_check = await asyncio.gather(
        loop.run_in_executor(None, check_url_validity, url),
        loop.run_in_executor(None, check_ssl, domain),
        loop.run_in_executor(None, check_domain_age, domain),
        loop.run_in_executor(None, check_blacklist, domain),
    )

    # Run the 2 async checks (need HTTP)
    short_check = await check_short_link(url)
    keyword_check = await check_suspicious_keywords(url)

    checks = [url_check, ssl_check, age_check, bl_check, short_check, keyword_check]
    score, risk, summary = compute_overall(checks)

    # Determine final URL (from short link expansion)
    final_url = url
    for f in short_check.findings:
        if f.message.startswith("  [") and "]" in f.message:
            # Last chain entry
            last = f.message.split("]", 1)[1].strip()
            if last.startswith("http"):
                final_url = last

    return AnalysisReport(
        url=url,
        final_url=final_url,
        checks=checks,
        overall_score=score,
        risk_level=risk,
        summary=summary,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve frontend
import os
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    @app.get("/")
    async def index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
