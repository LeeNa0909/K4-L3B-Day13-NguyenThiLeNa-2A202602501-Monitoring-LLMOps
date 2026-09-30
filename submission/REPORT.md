# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Thị Lệ Na
- **MSSV:** 2A202602501
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/LeeNa0909/K4-L3B-Day13-NguyenThiLeNa-2A202602501-Monitoring-LLMOps
- **Commit SHA cuối:** điền giá trị `git log -1 --format=%H` sau commit cuối
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602501`

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
| Số traces hợp lệ | Chưa kiểm tra trên Langfuse | Tối thiểu 10 | Danh sách Langfuse có nhiều hơn 10 trace/observation trong project cá nhân; đối chiếu ảnh `06-trace-list.png`. |
| Số PII leak | 0 | 0 | Log validator không phát hiện PII thô. |
| Latency P95 / TTFT P95 | Chưa đo | 2672 ms / 50 ms | Tính từ 74 event `response_sent` hiện có trong `data/logs.jsonl`. |
| Retrieval success rate | Chưa đo | 100% | Tính trên 74 event có `tool_success`; tổng cost `0.148344 USD`, tổng token `11888`. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** middleware xóa context cũ, nhận `x-request-id` hợp lệ hoặc sinh `req-` + 8 ký tự hex, bind vào structlog và trả lại trong response header.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, latency, TTFT, token, cost, quality và `correlation_id`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước file renderer; message/answer preview dùng scrubber, user ID chỉ ghi dưới dạng hash.
- **Cách kiểm chứng kết quả:** chạy `python scripts/validate_logs.py`, kiểm tra required fields, correlation IDs, enrichment và PII detector độc lập.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** mở đúng project `day13-k4-l3b-2A202602501` và đối chiếu thời gian chạy workload, số request và `correlation_id`.
- **Cấu trúc root/retrieval/generation observations:** root `day13-agent-request`, agent `lab-agent-run`, child `retrieval` và `generation`.
- **Cách nối trace với log:** dùng cùng `correlation_id` trong trace metadata và structured log.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** `day13-chat` version 1, labels `baseline` và `production`.
- **Version/label candidate:** `day13-chat` version 2, label `candidate`.
- **Trace ID version 1:** `e3c9c0afe69fe0536df85bd261bf83ab`; metadata có `correlation_id=req-a1b2c3d4`, `prompt_version=1`.
- **Trace ID version 2:** cần điền Trace ID thực tế từ trace được chạy với label `candidate`; không suy đoán ID.
- **Cách promote và rollback `production`:** chuyển label `production` sang version 2, chạy kiểm tra, rồi chuyển lại version 1. Ảnh `evidence/10-prompt-rollback.png` ghi nhận trạng thái cuối cùng: version 1 có `production` và `baseline`, version 2 có `candidate`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `scripts/dashboard.py` đọc `data/logs.jsonl` và hiển thị latency/TTFT, traffic, errors/retrieval, cost, tokens và quality trong cửa sổ 60 phút, refresh 30 giây.
- **SLO và lý do chọn:** SLO `99.5%` request có `latency_ms <= 3000` trong cửa sổ 28 ngày; ngưỡng phù hợp với contract dashboard latency P95 3000 ms.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; với 10,000 request, ngân sách lỗi tối đa là 50 request.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (>3000 ms/5m), `ElevatedErrorRate` (>2%/5m), `LowRetrievalSuccess` (<90%/10m); mỗi alert có Slack channel, owner và runbook Metrics → Logs → Traces trong `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30T08:03:00.970110Z`–`2026-09-30T08:03:03.624017Z` (UTC), theo request feature `monitoring` có correlation ID `req-14abcdef`.
- **Triệu chứng từ metrics:** ảnh `12-incident-metric.png` cho thấy P95 `5531.0 ms`, vượt SLO/dashboard threshold `3000 ms` và challenge threshold `2000 ms`; request đại diện trong log có latency `2652 ms`.
- **Log line và correlation ID liên quan:** evidence `13-incident-log.png`/log hiện tại ghi event `response_sent`, `correlation_id=req-14abcdef`, `feature=monitoring`, `latency_ms=2652`, `tool_name=retrieval`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** evidence `14-incident-trace.png` có Trace ID `b760cf0333314f4c7639a0ab323b4baa`, metadata cùng `correlation_id=req-14abcdef`; cây trace cho thấy span `retrieval` khoảng `2.50s` là span chậm.
- **Root cause:** incident `rag_slow` được challenge bật làm bước retrieval chậm khoảng 2.5 giây; generation vẫn có TTFT khoảng 50 ms.
- **Fix action:** tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`; health sau đó xác nhận cả ba incident đều `false`.
- **Preventive measure:** giữ alert `HighLatencyP95` với điều kiện P95 trên `3000 ms` trong `5m`, điều tra theo Metrics → Logs → Traces và kiểm tra retrieval span trước khi rollback prompt.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** dùng decorator Langfuse với `capture_input=False` và `capture_output=False` cho retrieval/generation để có waterfall nhưng không gửi raw prompt/output chứa PII.
- **Một lỗi/blocker đã gặp:** baseline thiếu correlation ID/enrichment; sau khi sửa middleware và logging, phải restart API để nạp decorator tracing mới và làm mới trace trên Langfuse.
- **Cách tìm nguyên nhân và xử lý:** đọc validator để xác định thiếu fields, sửa middleware/context binding/scrubber, rồi chuyển log CP0 ra ngoài repo và chạy lại workload.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics khoanh vùng triệu chứng, log chọn request bằng `correlation_id`, trace xác định span retrieval/generation gây chậm hoặc lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** các trường này giúp so sánh regression, kiểm soát chi phí, đặt ngưỡng vận hành và khôi phục version an toàn.
- **Điều quan trọng nhất đã học:** correlation ID là điểm nối giữa ba lớp quan sát và phải được tạo trước khi ghi log/tracing.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** ảnh rollback hiện chỉ ghi nhận trạng thái cuối sau rollback, chưa có ảnh riêng cho thời điểm promote version 2; cần bổ sung Trace ID version 2 của prompt `candidate`, xử lý lại ảnh metadata nếu còn lộ public key, và điền commit SHA cuối sau khi commit báo cáo.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace sau khi thay ảnh 13/14 bằng cùng request `req-14abcdef`.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret; cần thay ảnh 08 nếu còn dòng public key.
- [x] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
