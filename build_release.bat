rm dist/*

python -m pip install -U -r requirements.txt

python -m bumpver update --%1

python -m build

python -m twine check dist/*
python -m twine upload dist/*
