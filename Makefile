PYENV=.env-arm64
PYTHON=source $(PYENV)/bin/activate && python


$(PYENV)/.venv_created:
		python3.12 -m venv $(PYENV)
		touch $@

venv: $(PYENV)/.venv_created
.PHONY: venv


$(PYENV)/.deps_installed: requirements.txt
		$(PYTHON) -m pip install -r $^
		touch $@

install_deps: $(PYENV)/.deps_installed
.PHONY: install_deps

setup: venv install_deps
.PHONY: setup



run:
	$(PYTHON) main.py

