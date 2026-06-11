"""Link Safe — Pydantic data models."""

from pydantic import BaseModel


# ── Request ──
class AnalyzeRequest(BaseModel):
    url: str


# ── Single finding within a dimension ──
class Finding(BaseModel):
    severity: str   # "info" | "warn" | "danger"
    message: str


# ── One dimension's result ──
class DimensionResult(BaseModel):
    dimension: str       # e.g. "url_validity", "ssl", "domain_age"
    label: str           # e.g. "URL 合法性"
    status: str          # "pass" | "warn" | "fail"
    score: int           # 0-100
    detail: str
    findings: list[Finding]


# ── Full report ──
class AnalysisReport(BaseModel):
    url: str
    final_url: str
    checks: list[DimensionResult]
    overall_score: int       # 0-100
    risk_level: str          # "low" | "medium" | "high" | "critical"
    summary: str
