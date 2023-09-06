#!/bin/bash
mkdocs gh-deploy
rm -rf ./site
rm -rf ./dist

python3 -m build
twine upload dist/*