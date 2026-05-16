

run:
	$(error "Not Implemented Error")


install:
	uv sync


debug:
	$(error "Not Implemented Error")


clean:
	@rm -rfv $(find . -type d -name "__pycache__")


lint:
	@flake8 .
	@mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs


lint-strict:
	@flake8 .
	@mypy . --strict
