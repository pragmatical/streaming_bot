.PHONY: install run dev lint test

PY=python3
PIP=pip3

install:
	$(PIP) install -r requirements.txt

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

dev: install run
