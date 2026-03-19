#!/usr/bin/env bash

PYTHON_ENV=$1

python3 -m venv ./$PYTHON_ENV \
    && export PATH=./$PYTHON_ENV/bin:$PATH \
    && grep -qxF "source $(pwd)/$PYTHON_ENV/bin/activate" ~/.bashrc || echo "source $(pwd)/$PYTHON_ENV/bin/activate" >> ~/.bashrc

source ./$PYTHON_ENV/bin/activate

if [ -f "./requirements.txt" ]; then
  pip3 install -r "./requirements.txt"
elif [ -f "./requirements/requirements.txt" ]; then
  pip3 install -r "./requirements/requirements.txt"
else
  pip3 install -r "/workspaces/ai-aip/requirements/requirements.txt"
fi

# Ensure CPU-only PyTorch (no CUDA/GPU in Codespace)
./$PYTHON_ENV/bin/pip uninstall -y nvidia-cublas-cu12 nvidia-cuda-cupti-cu12 nvidia-cuda-nvrtc-cu12 nvidia-cuda-runtime-cu12 nvidia-cufft-cu12 nvidia-cufile-cu12 nvidia-curand-cu12 nvidia-cusparse-cu12 nvidia-cusparselt-cu12 nvidia-nccl-cu12 nvidia-nvjitlink-cu12 nvidia-nvshmem-cu12 nvidia-nvtx-cu12 2>/dev/null || true
./$PYTHON_ENV/bin/pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu 2>/dev/null || true
