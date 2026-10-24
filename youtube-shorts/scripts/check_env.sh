#!/bin/bash
export MAMBA_ROOT_PREFIX=~/micromamba
MM=~/mdtools/bin/micromamba
$MM run -n md gmx --version 2>&1 | grep -iE "gromacs version|gpu support|SIMD" || echo GMX_FAIL
echo "--- WSL GPU libs ---"
ls /usr/lib/wsl/lib/ 2>/dev/null | head -4
echo "--- MDAnalysis ---"
$MM run -n md python -c "import MDAnalysis; print('MDAnalysis', MDAnalysis.__version__)"
