# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:**
- **MSSV:**
- **Lớp:** K4-L3B
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-<MSSV>`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Baseline thiếu correlation/enrichment; sau CP1 đã đạt. |
| `validate_dashboard.py` | 6/6 | 6/6 | Contract đủ sáu panel. |
| `pytest` | 22 passed | 24 passed | Thêm test CCCD và thẻ thanh toán. |
| Số traces hợp lệ | Chưa kiểm tra trên Langfuse | Chưa điền | Cần đối chiếu danh sách trace trong project cá nhân. |
| Số PII leak | 0 | 0 | Log validator không phát hiện PII thô. |
| Latency P95 / TTFT P95 | Chưa đo | 2047.5 ms / 50 ms | Tính từ 63 event `response_sent` hiện có. |
| Retrieval success rate | Chưa đo | 100% | Tính trên các event có `tool_success`. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** middleware xóa context cũ, nhận `x-request-id` hợp lệ hoặc sinh `req-` + 8 ký tự hex, bind vào structlog và trả lại trong response header.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, latency, TTFT, token, cost, quality và `correlation_id`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước file renderer; message/answer preview dùng scrubber, user ID chỉ ghi dưới dạng hash.
- **Cách kiểm chứng kết quả:** chạy `python scripts/validate_logs.py`, kiểm tra required fields, correlation IDs, enrichment và PII detector độc lập.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** mở đúng project `day13-k4-l3b-<MSSV>` và đối chiếu thời gian chạy workload, số request và `correlation_id`.
- **Cấu trúc root/retrieval/generation observations:** root `day13-agent-request`, agent `lab-agent-run`, child `retrieval` và `generation`.
- **Cách nối trace với log:** dùng cùng `correlation_id` trong trace metadata và structured log.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** Chưa điền; cần tạo và xác nhận trên Langfuse.
- **Version/label candidate:** Chưa điền; cần tạo và xác nhận trên Langfuse.
- **Trace ID của mỗi version:** Chưa điền sau khi chạy hai label trên project cá nhân.
- **Cách promote và rollback `production`:** chuyển label `production` sang version 2, chạy kiểm tra, rồi chuyển lại version 1; bổ sung trace ID và ảnh evidence sau khi thực hiện.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `scripts/dashboard.py` đọc `data/logs.jsonl` và hiển thị latency/TTFT, traffic, errors/retrieval, cost, tokens và quality trong cửa sổ 60 phút, refresh 30 giây.
- **SLO và lý do chọn:** SLO `99.5%` request có `latency_ms <= 3000` trong cửa sổ 28 ngày; ngưỡng phù hợp với contract dashboard latency P95 3000 ms.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; với 10,000 request, ngân sách lỗi tối đa là 50 request.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (>3000 ms/5m), `ElevatedErrorRate` (>2%/5m), `LowRetrievalSuccess` (<90%/10m); mỗi alert có Slack channel, owner và runbook Metrics → Logs → Traces trong `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30T04:00:27Z`–`2026-09-30T04:00:41Z` (UTC), theo các request challenge feature `monitoring`.
- **Triệu chứng từ metrics:** baseline P95 `226.1 ms`; challenge P95 `2688.8 ms`, vượt threshold `2000 ms`. Năm request challenge có `latency_ms` từ `2664` đến `2690 ms`.
- **Log line và correlation ID liên quan:** event `response_sent`, `correlation_id=req-36d08bf3`, `feature=monitoring`, `latency_ms=2690`, `tool_name=retrieval`, `tool_success=true`. Các ID challenge còn lại: `req-103de8b7`, `req-75a84bfd`, `req-81bd244a`, `req-675b22cf`.
- **Trace ID và span gây ảnh hưởng:** Chưa điền trace ID; mở trace Langfuse có metadata `correlation_id=req-36d08bf3` và xác nhận span `retrieval` là span chậm.
- **Root cause:** incident `rag_slow` được challenge bật làm bước retrieval chậm khoảng 2.5 giây; generation vẫn có TTFT khoảng 50 ms.
- **Fix action:** tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`; health sau đó xác nhận cả ba incident đều `false`.
- **Preventive measure:** giữ alert `HighLatencyP95` với điều kiện P95 trên `3000 ms` trong `5m`, điều tra theo Metrics → Logs → Traces và kiểm tra retrieval span trước khi rollback prompt.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** dùng decorator Langfuse với `capture_input=False` và `capture_output=False` cho retrieval/generation để có waterfall nhưng không gửi raw prompt/output chứa PII.
- **Một lỗi/blocker đã gặp:** baseline thiếu correlation ID/enrichment; browser session hiện chưa khả dụng nên chưa thể tự lấy trace ID và ảnh prompt rollback.
- **Cách tìm nguyên nhân và xử lý:** đọc validator để xác định thiếu fields, sửa middleware/context binding/scrubber, rồi chuyển log CP0 ra ngoài repo và chạy lại workload.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics khoanh vùng triệu chứng, log chọn request bằng `correlation_id`, trace xác định span retrieval/generation gây chậm hoặc lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** các trường này giúp so sánh regression, kiểm soát chi phí, đặt ngưỡng vận hành và khôi phục version an toàn.
- **Điều quan trọng nhất đã học:** correlation ID là điểm nối giữa ba lớp quan sát và phải được tạo trước khi ghi log/tracing.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** cần hoàn tất prompt v1/v2, promote/rollback trên Langfuse, ghi trace IDs và chụp evidence runtime trước khi nộp.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
