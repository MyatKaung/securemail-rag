.PHONY: test test-ci lint audit

test:
	python -m pytest -q

test-ci:
	python -m pytest -q --disable-warnings --maxfail=1

lint:
	ruff check src tests

audit:
	@echo "Follow tasks/rubric_audit.md with Codex; this target is a placeholder for a future automated audit."
