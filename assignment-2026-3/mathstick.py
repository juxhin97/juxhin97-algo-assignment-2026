# ==========================================================
# Εργασία Αλγορίθμων 2026 
# Παραδοτέο 3: Γρίφοι με Σπίρτα (MathSticks Solver)
# Όνομα: Γιουτζίν Τσάτσα (Juxhin Caca)
# ΑΜ: 8150141
# ==========================================================

import argparse
import sys
import json
import re

# 1. Αναπαράσταση ψηφίων σε 7-segment display (0-9)
# 0: middle, 1: top, 2: top-right, 3: bottom-right, 4: bottom, 5: bottom-left, 6: top-left
DIGITS_SEGMENTS = {
    0: {1, 2, 3, 4, 5, 6},
    1: {2, 3},
    2: {0, 1, 2, 4, 5},
    3: {0, 1, 2, 3, 4},
    4: {0, 2, 3, 6},
    5: {0, 1, 3, 4, 6},
    6: {0, 1, 3, 4, 5, 6},
    7: {1, 2, 3, 6},
    8: {0, 1, 2, 3, 4, 5, 6},
    9: {0, 1, 2, 3, 4, 6}
}

def parse_arguments():
    """Διαχειρίζομαι ορίσματα από τη γραμμή εντολών."""
    parser = argparse.ArgumentParser(description="MathStick Puzzle Solver using DFS with Pruning.")
    parser.add_argument("--problem", type=str, required=True, help="Η εξίσωση προς επίλυση (π.χ. '0+0=1')")
    parser.add_argument("--max-k", type=int, default=2, help="Μέγιστος αριθμός επιτρεπόμενων κινήσεων (default: 2)")
    return parser.parse_args()

def parse_problem(problem_str):
    """
    Κνονικοποιώ και διασπώ την εξίσωση στα δομικά της μέρη.
    Επιστρέφει: (str_num1, operator, str_num2, str_num3) και τη συνολική δομή των slots.
    """
    # Αφαίρεση κενών
    clean_str = re.sub(r'\s+', '', problem_str)
    match = re.match(r'^(\d+)([+\-])(\d+)=(\d+)$', clean_str)
    if not match:
        print("Error: Invalid problem format.", file=sys.stderr)
        sys.exit(1)
        
    num1, op, num2, num3 = match.groups()
    return num1, op, num2, num3
