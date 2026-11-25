#!/usr/bin/env bash
# Build + solve both gyroscope models with COMSOL Multiphysics 6.3 (Linux/macOS).
# Usage: TFG_MESH=2 TFG_PAPER=0 ./run_comsol_linux.sh
set -e
cd "$(dirname "$0")"
COMSOL=${COMSOL:-comsol}
$COMSOL compile TFG_SchemeI_Chevron.java
$COMSOL compile TFG_SchemeII_Conventional.java
$COMSOL batch -inputfile TFG_SchemeI_Chevron.class -nosave
$COMSOL batch -inputfile TFG_SchemeII_Conventional.class -nosave
python3 ../generator/compare_comsol_runs.py .
