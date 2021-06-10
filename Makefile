format:
	black pytermgui
typecheck:
	mypy --show-error-codes --disable-error-code attr-defined pytermgui
lint:
	make format && pylint pytermgui && make typecheck

