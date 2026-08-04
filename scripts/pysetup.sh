#!/usr/bin/env bash

PYTHON_ENV=$1

python3 -m venv ./$PYTHON_ENV \
    && export PATH=./$PYTHON_ENV/bin:$PATH \
    && grep -qxF "source $(pwd)/$PYTHON_ENV/bin/activate" ~/.bashrc || echo "source $(pwd)/$PYTHON_ENV/bin/activate" >> ~/.bashrc

source ./$PYTHON_ENV/bin/activate

pip3 install --upgrade pip wheel

if [ -f "./requirements.txt" ]; then
  pip3 install --extra-index-url https://download.pytorch.org/whl/cpu -r "./requirements.txt"
elif [ -f "./requirements/requirements.txt" ]; then
  pip3 install --extra-index-url https://download.pytorch.org/whl/cpu -r "./requirements/requirements.txt"
else
  pip3 install --extra-index-url https://download.pytorch.org/whl/cpu -r "/workspaces/ai-aip/requirements/requirements.txt"
fi
