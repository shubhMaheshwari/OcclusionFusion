#!/bin/bash

# Compile cpp subsampling
cd cpp_subsampling
python3.7 setup.py build_ext --inplace
cd ..

# Compile cpp neighbors
cd cpp_neighbors
python3.7 setup.py build_ext --inplace
cd ..