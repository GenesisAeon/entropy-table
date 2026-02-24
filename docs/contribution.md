# Contribution Rules

1. Keep changes contract-first: update schema, then data, then tooling/tests.
2. Keep examples synthetic/placeholders unless explicitly requested otherwise.
3. Every domain must include `must_fail_tests` with at least two entries.
4. Every relation must include `must_fail_tests` with at least one entry.
5. For `closure_type: effectively_closed`, add meaningful `closure_notes`.
6. Run before commit:
   - `python tools/validate.py`
   - `pytest`
