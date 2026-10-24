#!/bin/bash
echo "USER=$(whoami) HOME=$HOME PWD=$PWD"
echo "PATH=$PATH"
echo "--- mdtools ---"
ls -la "$HOME/mdtools/bin/" 2>&1
echo "--- file binary ---"
file "$HOME/mdtools/bin/micromamba" 2>&1
echo "--- env list ---"
"$HOME/mdtools/bin/micromamba" env list 2>&1
echo "--- wsl lib ---"
ls /usr/lib/wsl/lib 2>&1 | head -4
echo "--- os ---"
uname -a
