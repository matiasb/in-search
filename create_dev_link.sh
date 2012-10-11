#!/bin/bash
cd ~/projects/deluge/in-search
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/insearch.egg-link ~/.config/deluge/plugins
rm -fr ./temp
