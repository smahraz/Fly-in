PY="python3"

run:
	uv run -m flyin maps/hard/02_capacity_hell.txt


install:
	uv sync


debug:
	$(PY) -m pdb -m flyin
	


clean:
	@rm -rfv $(find . -type d -name "__pycache__")
	@rm -rfv .mypy_cache/


lint:
	@flake8 . --exclude .venv,venv
	@mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs


lint-strict:
	@flake8 .
	@mypy . --strict
