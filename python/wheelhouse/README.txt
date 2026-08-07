Offline Python wheels for the air-gapped board.

Empty on purpose - fill it on a connected machine, then the whole project
folder is the air-gap bundle.

Build it (from python/):

    pip download -r requirements-dev.txt -d wheelhouse \
        --platform manylinux2014_aarch64 \
        --python-version 3.13 \
        --only-binary=:all:

Note --platform: the board is ARM64. Wheels built for your laptop's
architecture will not install there.

Install on the board (no network):

    pip install --no-index --find-links=wheelhouse -r requirements-dev.txt
