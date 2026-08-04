# Changelog

## Unreleased

- Locked local setup to CPU-only PyTorch with `torch==2.13.0+cpu` and configured `scripts/pysetup.sh` to use the PyTorch CPU wheel index.
- Updated local setup docs to recommend the helper install script and CPU-only dependency install path.
- Added `nohup.out` to `.gitignore` to keep transient logs out of the repository.
