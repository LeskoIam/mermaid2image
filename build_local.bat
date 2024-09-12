rm dist/*

python -m pip install -U -r requirements.txt

python -m build

python -m twine check dist/*

