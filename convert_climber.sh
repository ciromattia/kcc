#!/bin/bash
for f in ../mangal/The_Climber/*.pdf; do
    echo "Converting: $f"
    python3 kcc-c2e.py -d -p K810 -m -q "$f"
done
