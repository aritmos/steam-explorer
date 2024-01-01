env:
    #!/usr/bin/env zsh
    source .venv/bin/activate

lab:
    jupyter-lab --no-browser

book:
    clear && python3 -m src.scripts.analysis.hide && jb build src/book
