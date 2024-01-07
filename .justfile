lab:
    jupyter-lab --no-browser

book:
    clear && python3 -m src.scripts.analysis.hide && jb build src/book

publish:
    ghp-import -n -p -f src/book/_build/html
