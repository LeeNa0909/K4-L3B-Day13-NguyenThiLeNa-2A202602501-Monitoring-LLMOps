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

- **Cách tôi truyền correlation ID:** ngay khi request đi vào middleware, tôi xóa context cũ để tránh lẫn dữ liệu giữa hai request. Nếu header `x-request-id` có dạng hợp lệ thì giữ lại; nếu không, ứng dụng tự sinh ID dạng `req-` cộng với 8 ký tự hex. ID này được bind vào context, ghi vào log và trả lại qua response header.
- **Thông tin tôi giữ lại trong log:** log có `user_id_hash`, `session_id`, `feature`, `model`, `env`, `correlation_id`, latency, TTFT, token, cost và quality. User ID không được ghi nguyên văn.
- **Cách tôi xử lý PII:** trước khi JSON được render và ghi xuống `data/logs.jsonl`, `scrub_event` thay email, số điện thoại, CCCD và số thẻ bằng nhãn `[REDACTED_...]`. Vì vậy log vẫn hữu ích cho việc điều tra nhưng không chứa dữ liệu nhạy cảm dạng thô.
- **Cách tôi tự kiểm tra:** tôi chạy log validator sau khi chuyển log baseline cũ ra ngoài repo. Kết quả cuối là `100/100`, không có record thiếu field, không có correlation ID bị mất và không phát hiện PII.

## 5. Tracing và prompt versioning

- **Cách tôi xác nhận trace thuộc project của mình:** tôi chạy workload từ repo, sau đó mở đúng project `day13-k4-l3b-2A202602501` trên Langfuse và đối chiếu thời gian, tag `monitoring/qa` cùng `correlation_id` trong metadata.
- **Cấu trúc trace tôi tạo được:** một request có `lab-agent-run` làm observation chính, bên dưới có hai child observation là `retrieval` và `generation`. Nhờ vậy tôi có thể nhìn riêng thời gian retrieval và thời gian mô phỏng LLM.
- **Cách nối trace với log:** tôi dùng `correlation_id` làm điểm nối. Ví dụ request incident trong report dùng `req-14abcdef` ở cả `data/logs.jsonl` và metadata của trace.
- **Prompt tôi quản lý:** tên prompt là `day13-chat`. Version 1 giữ format ba biến `feature`, `docs`, `message`, đồng thời có label `baseline` và `production`. Version 2 thêm yêu cầu trả lời ngắn hơn và đang mang label `candidate`.
- **Trace version 1:** `e3c9c0afe69fe0536df85bd261bf83ab`; metadata có `correlation_id=req-a1b2c3d4` và `prompt_version=1`.
- **Trace version 2:** tôi sẽ điền Trace ID sau khi đối chiếu trace chạy với label `candidate`; tôi không tự điền một ID chưa kiểm chứng.
- **Rollback:** tôi chuyển `production` về version 1 sau khi thử version mới. Ảnh `evidence/10-prompt-rollback.png` thể hiện trạng thái cuối: version 1 có `production`/`baseline`, version 2 có `candidate`.

## 6. Dashboard, SLO và alerts

- **Dashboard:** tôi dùng `scripts/dashboard.py` để đọc log thực tế trong 60 phút gần nhất. Sáu panel giúp tôi nhìn latency/TTFT, traffic, errors/retrieval, cost, tokens và quality trên cùng một màn hình.
- **SLO:** tôi chọn mục tiêu `99.5%` request có `latency_ms <= 3000`. Với mục tiêu này, error budget là `0.5%`, tương đương tối đa 50 request trên mỗi 10.000 request.
- **Alert:** tôi giữ ba alert theo triệu chứng dễ nhận biết: `HighLatencyP95` trên `3000 ms` trong `5m`, `ElevatedErrorRate` trên `2%` trong `5m`, và `LowRetrievalSuccess` dưới `90%` trong `10m`. Runbook của từng alert đều bắt đầu từ Metrics, chuyển sang Logs rồi mới mở Traces.

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

Metric cho thấy latency bất thường trong khoảng `2026-09-30T08:03:00.970110Z`–`2026-09-30T08:03:03.624017Z`: P95 trên dashboard là `5531.0 ms`, vượt ngưỡng SLO `3000 ms` và challenge threshold `2000 ms`. Log `response_sent` có `correlation_id=req-14abcdef`, `latency_ms=2652`, `feature=monitoring`, `tool_name=retrieval` và `tool_success=true`. Trace `b760cf0333314f4c7639a0ab323b4baa` cùng correlation ID cho thấy span `retrieval` kéo dài khoảng `2.50s`, trong khi generation chỉ khoảng `152 ms` và TTFT là `50 ms`. Root cause là incident `rag_slow` làm bước retrieval bị chậm. Fix action là tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`. Preventive measure là duy trì alert `HighLatencyP95` trong `5m` và điều tra theo quy trình Metrics → Logs → Traces, đồng thời kiểm tra retrieval span trước khi rollback prompt.

## 8. Giải thích và tự đánh giá

- **Quyết định kỹ thuật tôi thấy quan trọng nhất:** tôi để `capture_input=False` và `capture_output=False` cho retrieval/generation. Nhờ vậy trace vẫn có waterfall, thời gian và metadata cần thiết nhưng không đẩy raw prompt/answer có thể chứa PII lên Langfuse.
- **Vấn đề tôi gặp:** sau khi sửa decorator tracing, API cũ vẫn còn chạy nên các trace mới chỉ hiện root observation. Tôi phải dừng process đang chiếm port 8000, khởi động lại API rồi gửi request mới; sau đó tree mới có `retrieval` và `generation`.
- **Cách tôi điều tra incident:** tôi không dùng thời gian client in ra từ load test. Tôi lấy `latency_ms` trong log/dashboard, chọn request `req-14abcdef`, rồi mở trace có cùng correlation ID để xác nhận retrieval là bước chậm.
- **Cách tôi hiểu luồng Metrics → Logs → Traces:** metrics chỉ cho tôi biết latency đang bất thường; log giúp khoanh đúng request; trace giúp chỉ ra retrieval là nguyên nhân trực tiếp. Ba lớp này phải trỏ về cùng request thì kết luận mới đáng tin.
- **Bài học về prompt, token/cost và SLO:** prompt version giúp biết request dùng bản nào, token/cost cho biết tác động vận hành, còn SLO/error budget giúp quyết định khi nào cần điều tra hoặc rollback.
- **Điều tôi rút ra:** correlation ID không phải chỉ để in ra response; nó là sợi dây nối từ request, structured log đến trace.
- **Phần còn thiếu:** tôi chưa bổ sung Trace ID version 2 của label `candidate`, ảnh metadata cần được kiểm tra để không lộ public key, và commit SHA cuối cần điền sau commit báo cáo.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace sau khi thay ảnh 13/14 bằng cùng request `req-14abcdef`.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret; cần thay ảnh 08 nếu còn dòng public key.
- [x] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
