#!/usr/bin/env bash
pushd docs
uv run sphinx-build -b html source build/html
uv run ghp-import -n -p build/html/
popd