from __future__ import annotations

import argparse
import html
import json
import statistics
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_records() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = _parse_timestamp(record.get("ts"))
        if timestamp is not None:
            record["_timestamp"] = timestamp
            records.append(record)
    return records


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def number(value: float | int | None, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{digits}f}"


def check(value: float | None, operator: str, threshold: float) -> str:
    if value is None:
        return "unknown"
    passed = value <= threshold if operator == "lte" else value >= threshold
    return "ok" if passed else "alert"


def metric(label: str, value: str, unit: str = "") -> str:
    return (
        '<div class="metric">'
        f'<span class="metric-label">{html.escape(label)}</span>'
        f'<span class="metric-value">{html.escape(value)}</span>'
        f'<span class="metric-unit">{html.escape(unit)}</span>'
        "</div>"
    )


def panel(
    panel_id: str,
    title: str,
    question: str,
    metrics: str,
    threshold_text: str,
    state: str,
) -> str:
    return f'''
      <section class="panel {html.escape(state)}" id="{html.escape(panel_id)}">
        <div class="panel-head">
          <h2>{html.escape(title)}</h2>
          <span class="status">{html.escape(state.upper())}</span>
        </div>
        <p class="question">{html.escape(question)}</p>
        <div class="metrics">{metrics}</div>
        <div class="threshold">Threshold/SLO: {html.escape(threshold_text)}</div>
      </section>
    '''


def render_dashboard() -> str:
    records = load_records()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=60)
    records = [record for record in records if record["_timestamp"] >= window_start]

    request_received = [r for r in records if r.get("event") == "request_received"]
    responses = [r for r in records if r.get("event") == "response_sent"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    latency_values = [float(r["latency_ms"]) for r in responses if r.get("latency_ms") is not None]
    ttft_values = [float(r["ttft_ms"]) for r in responses if r.get("ttft_ms") is not None]
    tool_values = [r["tool_success"] for r in records if isinstance(r.get("tool_success"), bool)]
    error_rate = len(failures) / len(request_received) * 100 if request_received else None
    retrieval_success = (
        sum(tool_values) / len(tool_values) * 100 if tool_values else None
    )
    total_cost = sum(float(r.get("cost_usd", 0)) for r in responses)
    total_input = sum(int(r.get("tokens_in", 0)) for r in responses)
    total_output = sum(int(r.get("tokens_out", 0)) for r in responses)
    quality_values = [float(r["quality_score"]) for r in responses if r.get("quality_score") is not None]
    quality_mean = statistics.mean(quality_values) if quality_values else None

    latency_p95 = percentile(latency_values, 95)
    traffic_rate = len(request_received) / 60
    cards = [
        panel(
            "latency",
            "Latency",
            "Request có chậm không?",
            metric("P50", number(percentile(latency_values, 50)), "ms")
            + metric("P95", number(latency_p95), "ms")
            + metric("P99", number(percentile(latency_values, 99)), "ms")
            + metric("TTFT P95", number(percentile(ttft_values, 95)), "ms"),
            "P95 <= 3000 ms",
            check(latency_p95, "lte", 3000),
        ),
        panel(
            "traffic",
            "Traffic",
            "Hệ thống nhận bao nhiêu request?",
            metric("Requests", str(len(request_received)), "requests")
            + metric("Rate", number(traffic_rate), "requests/minute"),
            "Rate >= 1 request/minute",
            check(traffic_rate, "gte", 1),
        ),
        panel(
            "errors",
            "Errors & retrieval",
            "Error rate có tăng, retrieval có fail không?",
            metric("Error rate", number(error_rate), "%")
            + metric("Retrieval success", number(retrieval_success), "%")
            + metric("Failures", str(len(failures)), "requests"),
            "Error rate <= 2%; retrieval success >= 90%",
            "ok"
            if (error_rate is None or error_rate <= 2)
            and (retrieval_success is None or retrieval_success >= 90)
            else "alert",
        ),
        panel(
            "cost",
            "Cost",
            "Chi phí có tăng bất thường không?",
            metric("Total", f"{total_cost:.6f}", "USD")
            + metric("Responses", str(len(responses)), "requests"),
            "Total <= 2.50 USD / 60 minutes",
            check(total_cost, "lte", 2.5),
        ),
        panel(
            "tokens",
            "Tokens",
            "Input/output token có dài bất thường không?",
            metric("Input", f"{total_input:,}", "tokens")
            + metric("Output", f"{total_output:,}", "tokens")
            + metric("Total", f"{total_input + total_output:,}", "tokens"),
            "Total <= 50,000 tokens / 60 minutes",
            check(total_input + total_output, "lte", 50000),
        ),
        panel(
            "quality",
            "Quality",
            "Quality proxy có dưới ngưỡng chấp nhận không?",
            metric("Mean score", number(quality_mean, 2), "score 0-1")
            + metric("Samples", str(len(quality_values)), "responses"),
            "Mean quality >= 0.75",
            check(quality_mean, "gte", 0.75),
        ),
    ]

    generated_at = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    return f'''<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="30">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>K4-L3B Monitoring Dashboard</title>
  <style>
    :root {{ color-scheme: dark; --bg: #0b1220; --card: #121c2d; --muted: #9fb0c7; --line: #27364f; --good: #3ddc97; --warn: #ffbd69; --bad: #ff7185; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 32px; background: var(--bg); color: #f4f7fb; font: 15px/1.45 Segoe UI, Arial, sans-serif; }}
    main {{ max-width: 1280px; margin: 0 auto; }}
    header {{ display: flex; justify-content: space-between; gap: 24px; align-items: end; margin-bottom: 24px; }}
    h1 {{ margin: 0 0 6px; font-size: 30px; }}
    .meta, .question, .threshold, footer {{ color: var(--muted); }}
    .meta {{ text-align: right; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .panel {{ padding: 20px; border: 1px solid var(--line); border-top: 4px solid var(--good); border-radius: 14px; background: var(--card); box-shadow: 0 8px 24px #0003; }}
    .panel.alert {{ border-top-color: var(--bad); }}
    .panel.unknown {{ border-top-color: var(--warn); }}
    .panel-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
    h2 {{ margin: 0; font-size: 21px; }}
    .status {{ color: var(--good); font-size: 11px; font-weight: 700; letter-spacing: .08em; }}
    .alert .status {{ color: var(--bad); }}
    .unknown .status {{ color: var(--warn); }}
    .question {{ margin: 8px 0 18px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
    .metric {{ min-height: 74px; padding: 10px; border: 1px solid var(--line); border-radius: 10px; background: #0d1626; }}
    .metric-label, .metric-unit {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric-value {{ display: block; margin: 5px 0 1px; font-size: 21px; font-weight: 700; }}
    .threshold {{ margin-top: 18px; padding-top: 12px; border-top: 1px solid var(--line); font-size: 13px; }}
    footer {{ margin-top: 24px; font-size: 13px; }}
    @media (max-width: 900px) {{ body {{ padding: 18px; }} header {{ display: block; }} .meta {{ margin-top: 10px; text-align: left; }} .grid {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 560px) {{ .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div><h1>K4-L3B Monitoring &amp; LLMOps</h1><div class="meta">Runtime dashboard from <code>data/logs.jsonl</code></div></div>
      <div class="meta">Time range: last 60 minutes<br>Refresh: 30 seconds<br>Generated: {html.escape(generated_at)}</div>
    </header>
    <div class="grid">{''.join(cards)}</div>
    <footer>Six panels: latency, traffic, errors/retrieval, cost, tokens, quality. Thresholds follow <code>config/dashboard.yaml</code>.</footer>
  </main>
</body>
</html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        body = render_dashboard().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local six-panel monitoring dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
