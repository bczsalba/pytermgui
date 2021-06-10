format:
	black pytermgui
typecheck:
	mypy --show-error-codes --disable-error-code attr-defined pytermgui
badge:
	python3 utils/create_badge.py
lint:
	pylint --exit-zero pytermgui

all:
	make format && make lint && make typecheck && make badge

