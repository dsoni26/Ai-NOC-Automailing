import re


def classify_severity(text: str) -> str:
    if not text:
        return "Low"

    text = text.lower()
    critical_keywords = ["server down", "down", "outage", "failed", "failure", "data loss", "critical", "crash", "unreachable"]
    high_keywords = ["cpu high", "memory spike", "disk full", "latency", "degraded", "slow", "timeout", "overload"]
    medium_keywords = ["warning", "partial", "intermittent", "retry", "degradation", "logging", "service restart"]
    low_keywords = ["info", "minor", "notice", "non-critical", "update", "maintenance"]

    for keyword in critical_keywords:
        if keyword in text:
            return "Critical"
    for keyword in high_keywords:
        if keyword in text:
            return "High"
    for keyword in medium_keywords:
        if keyword in text:
            return "Medium"
    for keyword in low_keywords:
        if keyword in text:
            return "Low"
    return "Medium"
