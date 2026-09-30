# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `fast_successful_requests`; `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút liên tục.
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Latency, xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` theo khoảng thời gian, lấy một `correlation_id` có latency cao.
  3. Mở trace cùng `correlation_id`, so sánh retrieval và generation.
- Mitigation tạm thời: tắt practice scenario, rollback prompt nếu generation bất thường, sau đó chạy lại một request kiểm tra.
- Owner: `student-2A202602501`

## Alert 2

- Tên: `ElevatedErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: error rate guardrail `2%`.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` trong 5 phút liên tục.
- Ảnh hưởng tới người dùng: một phần request không trả được câu trả lời hợp lệ.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Errors để phân biệt `request_failed` và retrieval failure.
  2. Lọc log theo `error_type`, `tool_success` và `correlation_id`.
  3. Mở trace cùng `correlation_id` để xác định observation lỗi.
- Mitigation tạm thời: tắt incident `tool_fail` nếu đang bật, giảm tải, và rollback thay đổi gần nhất nếu có evidence.
- Owner: `student-2A202602501`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success rate guardrail `90%`.
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90%` trong 10 phút liên tục.
- Ảnh hưởng tới người dùng: câu trả lời có thể thiếu context hoặc dùng fallback không đầy đủ.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Errors và xác nhận retrieval success rate.
  2. Lọc log có `tool_name`, `tool_success=false` và lấy `correlation_id` đại diện.
  3. Mở trace cùng ID, kiểm tra retrieval span và generation metadata.
- Mitigation tạm thời: phục hồi retrieval backend, tắt practice scenario, và chạy lại cùng input để xác nhận.
- Owner: `student-2A202602501`
