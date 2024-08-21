default: lint test tox build

venv:
	uv pip sync pyproject.toml

tox:
	uv run tox

tox-lint:
	uv run tox run -e type
	uv run tox run -e lint

test:
	uv run python -m pytest --cov=oil --cov-report html --cov-branch -vv

lint:
	uv run mypy src/ tests/
	uv run ruff format src/ tests/
	uv run ruff check src/ tests/

build: tox
	uv run hatch build

clean:
	rm -fr .venv/ dist/

.PHONY: clean build lint test tox tox-lint

