.PHONY:

build:
	del /Q /S .\dist\*
	python -m build
	copy .\dist\* .\versions

upload:
	python -m pip install twine --upgrade
	python -m twine upload dist/* --verbose

update:
	python -m pip install twine --upgrade
	python -m twine upload --repository pybencher dist/* --verbose