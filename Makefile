PROJECT = pytermgui

all:
	make format && make lint && make typecheck && make badge

format:
	black $(PROJECT)

typecheck:
	mypy --show-error-codes --disable-error-code attr-defined $(PROJECT)

badge:
	python3 utils/create_badge.py -c "make lint"

lint:
	pylint -d fixme --exit-zero $(PROJECT)
