import json
import os
from typing import Dict, Any

def get_metrics_data() -> list:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'metrics.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def analyze_metric_trends() -> str:
    """Tool for Data Analyst: Returns the last 14 days of metrics to identify trends."""
    data = get_metrics_data()
    if not data:
        return "No metrics data found."
    
    # We will format this into a readable string for the LLM
    summary = "Historical 14-Day Metrics:\n"
    for day in data:
        summary += f"Date: {day['date']} | DAU: {day['dau']} | Act%: {day['activation_conversion_pct']} | "+ \
                   f"Ret1D: {day['d1_retention_pct']} | P95 Latency: {day['p95_api_latency_ms']}ms | "+ \
                   f"Crash%: {day['crash_rate_pct']} | PaySuccess%: {day['payment_success_pct']} | "+ \
                   f"Adoption%: {day['feature_adoption_pct']}\n"
    return summary

def detect_anomalies() -> str:
    """Tool for Data Analyst: Analyzes the metrics file for statistical anomalies over the last 3 days compared to prior."""
    data = get_metrics_data()
    if len(data) < 5:
        return "Not enough data for anomaly detection."
    
    recent = data[-3:]
    baseline = data[:-3]
    
    def avg(lst, key):
        if not lst: return 0
        return sum(d[key] for d in lst) / len(lst)
    
    report = "Anomaly Detection Report (Last 3 Days vs Previous Baseline):\n"
    
    for metric in ["p95_api_latency_ms", "crash_rate_pct", "payment_success_pct"]:
        b_avg = avg(baseline, metric)
        r_avg = avg(recent, metric)
        diff = ((r_avg - b_avg) / b_avg) * 100 if b_avg > 0 else 0
        
        if abs(diff) > 10:  # > 10% change
            direction = "INCREASED" if diff > 0 else "DECREASED"
            report += f"- {metric} {direction} by {abs(diff):.1f}% (Baseline: {b_avg:.2f} -> Recent: {r_avg:.2f})\n"
            
    if report == "Anomaly Detection Report (Last 3 Days vs Previous Baseline):\n":
        return "No significant statistical anomalies detected."
    return report

def get_release_notes() -> str:
    """Tool to read the current release notes and known risks."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'release_notes.txt')
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "No release notes available."
