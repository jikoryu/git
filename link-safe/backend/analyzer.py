"""Link Safe — 6-dimension security analysis engine."""

import re
import ssl
import socket
import math
import datetime
from urllib.parse import urlparse

import whois

from models import DimensionResult, Finding

# ═══════════════════════════════════════
# Constants
# ═══════════════════════════════════════

SUSPICIOUS_TLDS = {
    ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".xyz", ".pw", ".cc",
    ".loan", ".work", ".click", ".link", ".buzz", ".icu", ".cyou",
    ".cfd", ".sbs", ".bond", ".rest", ".stream", ".live",
}

SHORT_LINK_DOMAINS = {
    "bit.ly", "t.co", "tinyurl.com", "ow.ly", "is.gd", "buff.ly",
    "goo.gl", "shorte.st", "adf.ly", "bc.vc", "bit.do", "cutt.ly",
    "db.tt", "git.io", "rebrand.ly", "shorturl.at", "snip.ly",
    "soo.gd", "v.gd", "x.co", "yourls.org", "zpr.io",
}

PHISHING_KEYWORDS = [
    "login", "signin", "verify", "confirm", "update", "account",
    "password", "credential", "bank", "banking", "paypal", "unlock",
    "suspended", "limited", "urgent", "security", "validate",
    "recover", "unusual", "activity", "unauthorized", "billing",
    "invoice", "refund", "expired", "deactivated",
]

HOMOGLYPH_MAP = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y",
    "і": "i", "х": "x", "ԁ": "d", "һ": "h", "ԛ": "q",
}

# ═══════════════════════════════════════
# Dimension 1: URL 合法性
# ═══════════════════════════════════════

def check_url_validity(url: str) -> DimensionResult:
    findings = []
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    score = 100

    # Protocol
    if parsed.scheme == "https":
        findings.append(Finding(severity="info", message="使用 HTTPS 加密协议"))
    elif parsed.scheme == "http":
        findings.append(Finding(severity="warn", message="使用 HTTP 明文协议，数据未加密"))
        score -= 15
    else:
        findings.append(Finding(severity="danger", message=f"未知协议: {parsed.scheme}"))
        score -= 30

    # IP address detection
    ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if ip_re.match(domain):
        findings.append(Finding(severity="danger", message="URL 使用 IP 地址直连，常见于钓鱼/恶意攻击"))
        score -= 25
    else:
        findings.append(Finding(severity="info", message="使用合法域名格式"))

    # @ sign attack
    if "@" in parsed.netloc:
        findings.append(Finding(severity="danger", message="URL 包含 @ 符号，可伪装为合法网站"))
        score -= 30
    else:
        findings.append(Finding(severity="info", message="未发现 @ 符号伪装"))

    # URL encoding ratio
    encoded = url.count("%")
    total = len(url)
    if total > 0 and encoded / total > 0.3:
        findings.append(Finding(severity="warn", message=f"URL 编码比例过高 ({encoded} 处)，可能隐藏恶意内容"))
        score -= 10

    # Domain length
    if len(domain) > 60:
        findings.append(Finding(severity="warn", message=f"域名过长 ({len(domain)} 字符)"))
        score -= 5

    # Suspicious TLD
    tld = "." + domain.split(".")[-1] if "." in domain else ""
    if tld.lower() in SUSPICIOUS_TLDS:
        findings.append(Finding(severity="warn", message=f"使用高风险 TLD: {tld}，常见于钓鱼/欺诈网站"))
        score -= 15

    # Homoglyph attack
    has_homo = any(c in HOMOGLYPH_MAP for c in domain)
    if has_homo:
        findings.append(Finding(severity="danger", message="域名包含 Unicode 同形异义字符，可能伪装为知名网站"))
        score -= 25
    else:
        findings.append(Finding(severity="info", message="未检测到同形异义字符"))

    # Too many subdomains
    subdomain_count = domain.count(".") if not ip_re.match(domain) else 0
    if subdomain_count > 4:
        findings.append(Finding(severity="warn", message=f"过多子域名 ({subdomain_count} 级)，可能是恶意子域名"))
        score -= 8

    score = max(0, min(100, score))
    status = "pass" if score >= 80 else ("warn" if score >= 50 else "fail")
    return DimensionResult(
        dimension="url_validity",
        label="URL 合法性",
        status=status,
        score=score,
        detail=f"URL 结构分析完成，得分 {score}/100",
        findings=findings,
    )


# ═══════════════════════════════════════
# Dimension 2: SSL 证书有效性
# ═══════════════════════════════════════

def check_ssl(domain: str) -> DimensionResult:
    findings = []
    score = 100

    if not domain:
        return DimensionResult(
            dimension="ssl", label="SSL 证书",
            status="fail", score=0, detail="无法解析域名",
            findings=[Finding(severity="danger", message="无效的域名")]
        )

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Issuer
                issuer = dict(x[0] for x in cert.get("issuer", []))
                cn = issuer.get("commonName", "Unknown")
                findings.append(Finding(severity="info", message=f"证书颁发者: {cn}"))

                # Expiry
                not_after = cert.get("notAfter", "")
                if not_after:
                    expire_date = datetime.datetime.strptime(
                        not_after, "%b %d %H:%M:%S %Y %Z"
                    )
                    days_left = (
                        expire_date - datetime.datetime.now(datetime.timezone.utc)
                    ).days
                    expire_str = expire_date.strftime("%Y-%m-%d")
                    if days_left < 0:
                        findings.append(Finding(severity="danger", message=f"SSL 证书已过期 ({expire_str})"))
                        score -= 40
                    elif days_left < 30:
                        findings.append(Finding(severity="warn", message=f"SSL 证书即将过期，剩余 {days_left} 天 ({expire_str})"))
                        score -= 15
                    else:
                        findings.append(Finding(severity="info", message=f"证书有效期至 {expire_str}，剩余 {days_left} 天"))

                # Subject Alternative Names
                san = cert.get("subjectAltName", [])
                if san:
                    domains = [d[1] for d in san if d[0] == "DNS"]
                    if len(domains) <= 3:
                        findings.append(Finding(severity="info", message=f"包含 {len(domains)} 个 SAN 域名"))
                    else:
                        findings.append(Finding(severity="warn", message=f"证书涵盖 {len(domains)} 个域名，可能是共享证书"))

    except ssl.SSLCertVerificationError as e:
        findings.append(Finding(severity="danger", message=f"证书验证失败: {str(e)[:80]}"))
        score -= 35
    except ssl.SSLError as e:
        findings.append(Finding(severity="danger", message=f"SSL 错误: {str(e)[:80]}"))
        score -= 30
    except socket.timeout:
        findings.append(Finding(severity="warn", message="SSL 连接超时"))
        score -= 15
    except ConnectionRefusedError:
        findings.append(Finding(severity="fail", message="443 端口连接被拒绝，可能未启用 HTTPS"))
        score -= 20
    except OSError as e:
        findings.append(Finding(severity="warn", message=f"连接失败: {str(e)[:80]}"))
        score -= 20
    except Exception as e:
        findings.append(Finding(severity="warn", message=f"SSL 检测异常: {str(e)[:80]}"))
        score -= 15

    score = max(0, min(100, score))
    status = "pass" if score >= 80 else ("warn" if score >= 50 else "fail")
    return DimensionResult(
        dimension="ssl",
        label="SSL 证书",
        status=status,
        score=score,
        detail=f"SSL 证书检测完成，得分 {score}/100",
        findings=findings,
    )


# ═══════════════════════════════════════
# Dimension 3: 域名年龄
# ═══════════════════════════════════════

def check_domain_age(domain: str) -> DimensionResult:
    findings = []
    score = 100

    if not domain:
        return DimensionResult(
            dimension="domain_age", label="域名年龄",
            status="fail", score=0, detail="无法解析域名",
            findings=[Finding(severity="danger", message="无效的域名")]
        )

    try:
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]

        if created is None:
            findings.append(Finding(severity="warn", message="无法获取域名注册日期（WHOIS 隐私保护）"))
            score -= 10
        else:
            now = datetime.datetime.now(datetime.timezone.utc)
            if created.tzinfo is None:
                created = created.replace(tzinfo=datetime.timezone.utc)
            age_days = (now - created).days
            created_str = created.strftime("%Y-%m-%d")

            if age_days < 30:
                findings.append(Finding(severity="danger", message=f"域名仅注册 {age_days} 天 ({created_str})，新域名是钓鱼攻击的常见特征"))
                score -= 35
            elif age_days < 180:
                findings.append(Finding(severity="warn", message=f"域名注册不足 6 个月 ({age_days} 天, {created_str})"))
                score -= 15
            elif age_days < 730:
                findings.append(Finding(severity="info", message=f"域名已注册 {age_days} 天（约 {age_days // 365} 年），{created_str}"))
            else:
                findings.append(Finding(severity="info", message=f"域名已注册 {age_days} 天（约 {age_days // 365} 年），{created_str}，可信度较高"))

        # Registrar
        registrar = w.registrar
        if registrar:
            findings.append(Finding(severity="info", message=f"注册商: {registrar}"))

    except whois.parser.PywhoisError:
        findings.append(Finding(severity="warn", message="WHOIS 查询无结果，域名可能未注册或已被删除"))
        score -= 20
    except Exception as e:
        findings.append(Finding(severity="warn", message=f"WHOIS 查询失败: {str(e)[:80]}"))
        score -= 10

    score = max(0, min(100, score))
    status = "pass" if score >= 80 else ("warn" if score >= 50 else "fail")
    return DimensionResult(
        dimension="domain_age",
        label="域名年龄",
        status=status,
        score=score,
        detail=f"域名年龄检测完成，得分 {score}/100",
        findings=findings,
    )


# ═══════════════════════════════════════
# Dimension 4: 域名封禁/黑名单
# ═══════════════════════════════════════

# Built-in blacklist patterns (partial hashes / domain patterns of known phishing sites)
BLACKLIST_PATTERNS = [
    r"secure.*verify.*\.tk$",
    r".*banking.*\.ml$",
    r"account.*secure.*\.cf$",
    r"paypal.*login.*\.ga$",
    r"apple.*id.*verify.*\.xyz$",
    r"update.*payment.*\.top$",
    r".*-security.*\.loan$",
]

async def check_blacklist(url: str, domain: str) -> DimensionResult:
    import httpx
    from config import config

    findings = []
    score = 100

    if not domain:
        return DimensionResult(
            dimension="blacklist", label="域名封禁",
            status="fail", score=0, detail="无法解析域名",
            findings=[Finding(severity="danger", message="无效的域名")]
        )

    # ── 1. Local blacklist patterns ──
    matched = False
    for pattern in BLACKLIST_PATTERNS:
        if re.match(pattern, domain, re.IGNORECASE):
            findings.append(Finding(severity="danger", message=f"域名匹配已知钓鱼模式: {pattern}"))
            score -= 40
            matched = True

    if not matched:
        findings.append(Finding(severity="info", message="未匹配本地黑名单模式"))

    # ── 2. Suspicious keyword combinations ──
    domain_lower = domain.lower()
    danger_words = ["secure", "verify", "login", "account", "bank", "paypal", "appleid", "update", "confirm"]
    hit_count = sum(1 for w in danger_words if w in domain_lower)
    if hit_count >= 2:
        findings.append(Finding(severity="warn", message=f"域名包含 {hit_count} 个敏感关键词，可能伪装为合法服务"))
        score -= 15

    # ── 3. Google Safe Browsing API ──
    gsb_key = config.GOOGLE_SAFE_BROWSING_KEY
    if gsb_key:
        try:
            gsb_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={gsb_key}"
            gsb_body = {
                "client": {"clientId": "link-safe", "clientVersion": "1.0"},
                "threatInfo": {
                    "threatTypes": [
                        "MALWARE",
                        "SOCIAL_ENGINEERING",
                        "UNWANTED_SOFTWARE",
                        "POTENTIALLY_HARMFUL_APPLICATION",
                    ],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}],
                },
            }
            async with httpx.AsyncClient(timeout=10) as client:
                gsb_resp = await client.post(gsb_url, json=gsb_body)
                if gsb_resp.status_code == 200:
                    gsb_data = gsb_resp.json()
                    matches = gsb_data.get("matches", [])
                    if matches:
                        threats = {m.get("threatType", "UNKNOWN") for m in matches}
                        findings.append(Finding(
                            severity="danger",
                            message=f"Google Safe Browsing 标记为恶意: {', '.join(threats)}"
                        ))
                        score -= 50
                    else:
                        findings.append(Finding(severity="info", message="Google Safe Browsing: 安全，未列入黑名单"))
                elif gsb_resp.status_code == 400:
                    findings.append(Finding(severity="info", message="Google Safe Browsing: API key 无效，已跳过"))
        except Exception as e:
            findings.append(Finding(severity="warn", message=f"Google Safe Browsing 查询失败: {str(e)[:60]}"))
    else:
        findings.append(Finding(severity="info", message="未配置 Google Safe Browsing API key，跳过云端黑名单检测"))

    score = max(0, min(100, score))
    status = "pass" if score >= 80 else ("warn" if score >= 50 else "fail")
    return DimensionResult(
        dimension="blacklist",
        label="域名封禁/黑名单",
        status=status,
        score=score,
        detail=f"黑名单检测完成，得分 {score}/100",
        findings=findings,
    )


# ═══════════════════════════════════════
# Dimension 5: 短链接展开
# ═══════════════════════════════════════

async def check_short_link(url: str) -> DimensionResult:
    import httpx
    findings = []
    score = 100
    parsed = urlparse(url)
    domain = parsed.hostname or ""

    is_short = any(s in domain.lower() for s in SHORT_LINK_DOMAINS)

    if not is_short:
        findings.append(Finding(severity="info", message="不是已知短链接，无需展开"))
        return DimensionResult(
            dimension="short_link", label="短链接展开",
            status="pass", score=100, detail="非短链接，满分通过",
            findings=findings,
        )

    findings.append(Finding(severity="info", message=f"检测到短链接服务: {domain}"))

    # Expand up to 5 levels
    expansion_chain = [url]
    current_url = url
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            for level in range(5):
                resp = await client.get(current_url, headers={"User-Agent": "LinkSafe/1.0"})
                if resp.status_code in (301, 302, 303, 307, 308):
                    next_url = resp.headers.get("location", "")
                    if not next_url:
                        break
                    # Handle relative URLs
                    if next_url.startswith("/"):
                        p = urlparse(current_url)
                        next_url = f"{p.scheme}://{p.netloc}{next_url}"
                    expansion_chain.append(next_url)
                    current_url = next_url
                else:
                    break
    except Exception as e:
        findings.append(Finding(severity="warn", message=f"短链接展开中断: {str(e)[:60]}"))
        score -= 10

    if len(expansion_chain) > 1:
        findings.append(Finding(severity="info", message=f"展开 {len(expansion_chain)-1} 层跳转"))
        # Show the chain
        for i, u in enumerate(expansion_chain):
            findings.append(Finding(severity="info", message=f"  [{i}] {u[:80]}"))

        # Check final destination
        final = expansion_chain[-1]
        final_parsed = urlparse(final)
        final_domain = final_parsed.hostname or ""

        if final_domain != domain:
            findings.append(Finding(severity="warn", message=f"目标域名 {final_domain} 与短链域名 {domain} 不同"))

        # IP destination
        ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        if ip_re.match(final_domain):
            findings.append(Finding(severity="danger", message=f"最终目标为 IP 地址: {final_domain}"))
            score -= 25

    score = max(0, min(100, score))
    status = "pass" if score >= 80 else ("warn" if score >= 50 else "fail")
    return DimensionResult(
        dimension="short_link",
        label="短链接展开",
        status=status,
        score=score,
        detail=f"短链接检测完成，展开 {len(expansion_chain)-1} 层，得分 {score}/100",
        findings=findings,
    )


# ═══════════════════════════════════════
# Dimension 6: 可疑关键词
# ═══════════════════════════════════════

async def check_suspicious_keywords(url: str) -> DimensionResult:
    import httpx
    findings = []
    score = 100

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "LinkSafe/1.0 Security Scanner"},
                follow_redirects=True,
            )
            text = resp.text[:10000].lower()
            title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE)
            title = title_match.group(1) if title_match else ""

            # Remove HTML tags for clean text
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = re.sub(r"\s+", " ", clean)

            # Count phishing keywords
            hits = {}
            for kw in PHISHING_KEYWORDS:
                count = len(re.findall(r"\b" + re.escape(kw) + r"\b", clean))
                if count > 0:
                    hits[kw] = count

            total_hits = sum(hits.values())
            unique_hits = len(hits)

            if unique_hits >= 5:
                findings.append(Finding(severity="danger", message=f"页面包含 {unique_hits} 个钓鱼/敏感关键词，高度可疑"))
                score -= 35
                for k, c in list(hits.items())[:5]:
                    findings.append(Finding(severity="warn", message=f"  \"{k}\" 出现 {c} 次"))
            elif unique_hits >= 2:
                findings.append(Finding(severity="warn", message=f"页面包含 {unique_hits} 个敏感关键词，需注意"))
                score -= 15
            elif unique_hits >= 1:
                findings.append(Finding(severity="info", message=f"页面包含 {unique_hits} 个常见关键词"))
            else:
                findings.append(Finding(severity="info", message="未检测到敏感关键词"))

            # Title analysis
            if title:
                findings.append(Finding(severity="info", message=f"页面标题: {title[:100]}"))

            # Page size
            text_len = len(resp.text)
            if text_len < 200:
                findings.append(Finding(severity="warn", message=f"页面内容极短 ({text_len} 字符)，可能是钓鱼占位页"))
                score -= 10

    except Exception as e:
        findings.append(Finding(severity="warn", message=f"无法获取页面内容: {str(e)[:80]}"))
        score -= 15

    score = max(0, min(100, score))
    status = "pass" if score >= 80 else ("warn" if score >= 50 else "fail")
    return DimensionResult(
        dimension="suspicious_words",
        label="可疑关键词",
        status=status,
        score=score,
        detail=f"关键词检测完成，命中 {sum(1 for f in findings if f.severity != 'info')} 个可疑项，得分 {score}/100",
        findings=findings,
    )


# ═══════════════════════════════════════
# Master: Run all 6 checks
# ═══════════════════════════════════════

WEIGHTS = {
    "url_validity": 0.15,
    "ssl": 0.25,
    "domain_age": 0.10,
    "blacklist": 0.25,
    "short_link": 0.10,
    "suspicious_words": 0.15,
}

RISK_LABELS = {80: "low", 55: "medium", 30: "high", 0: "critical"}

def compute_overall(checks: list[DimensionResult]) -> tuple[int, str, str]:
    """Compute weighted overall score and risk level."""
    total = sum(WEIGHTS.get(c.dimension, 0.1) * c.score for c in checks)
    weights_sum = sum(WEIGHTS.get(c.dimension, 0.1) for c in checks)
    score = round(total / weights_sum) if weights_sum > 0 else 0

    if score >= 80:
        risk = "low"
        summary = "✅ 该网站整体安全性良好，未发现严重风险。建议保持日常警惕。"
    elif score >= 55:
        risks = [c.label for c in checks if c.status in ("warn", "fail")]
        summary = f"⚠️ 该网站存在一定风险（{', '.join(risks[:3])}需关注）。请谨慎访问，不要输入个人敏感信息。"
    elif score >= 30:
        risks = [c.label for c in checks if c.status == "fail"]
        summary = f"🔴 该网站风险较高（{', '.join(risks[:3])}严重异常）。强烈建议不要访问或输入任何信息。"
    else:
        summary = "🚨 该网站极可能是恶意/钓鱼网站。请立即关闭页面，不要进行任何操作。"

    return score, risk, summary
