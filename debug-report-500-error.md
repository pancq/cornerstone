# Debug Session: report-500-error

Status: OPEN
Owner: AI Assistant

## Symptoms
- Frontend shows: "Failed to generate report: AxiosError: 500"
- Trigger: POST /api/reports/monthly/generate

## Quick Hypotheses (falsifiable)
1) Wrong model import in report_generator.py: `from src.models.inspection_device_result` (module does not exist) → ImportError at runtime.
2) Wrong field names: using `inspected_at`/`result == 'online'` while model defines `scanned_at` (DateTime) and `is_online` (Boolean) → ORM compilation/runtime error.
3) TZ mismatch in queries (aware vs naive) on DateTime filters → DBAPI DataError.
4) Missing/empty inspection data for the selected month → division by zero or None handling fault.
5) PDF rendering path issues (fonts/images) → exception thrown and captured as 500.

## Plan
- Instrument collect_report_data() around the availability query to emit debug events (counts, first/last timestamp, SQL errors).
- If hypothesis (1)/(2) is confirmed, apply minimal patch:
  - Import: `from src.models.inspection import InspectionDeviceResult`
  - Query by `scanned_at` in [month_start, next_month)
  - Online filter: `InspectionDeviceResult.is_online.is_(True)`

## Verification Checklist
- Call /monthly/generate after patch → expect 200 and valid PDF.
- Cross-check summary page shows availability instead of "暂无数据".
- Confirm no new 500s in logs.

## Cleanup
- Remove instrumentation after user confirms the fix.
