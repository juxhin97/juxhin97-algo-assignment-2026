# ==========================================================
# Εργασία Αλγορίθμων 2026 
# Παραδοτέο 3: Γρίφοι με Σπίρτα (MathSticks Solver)
# Όνομα: Γιουτζίν Τσάτσα (Juxhin Caca)
# AM: 8150141
# ==========================================================

import argparse
import sys
import re

# Αναπαράσταση ψηφίων σε 7-segment display (0-9)
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
    """Διαχείριση ορισμάτων από τη γραμμή εντολών."""
    parser = argparse.ArgumentParser(description="MathStick Puzzle Solver - Milestone 2")
    parser.add_argument("--problem", type=str, required=True, help="Η εξίσωση προς επίλυση (π.χ. '0+0=1')")
    parser.add_argument("--max-k", type=int, default=2, help="Μέγιστος αριθμός κινήσεων")
    return parser.parse_args()

def parse_problem(problem_str):
    """Κανονικοποιεί και διασπά την εξίσωση στα δομικά της μέρη."""
    clean_str = re.sub(r'\s+', '', problem_str)
    match = re.match(r'^(\d+)([+\-])(\d+)=(\d+)$', clean_str)
    if not match:
        print("Error: Invalid problem format.", file=sys.stderr)
        sys.exit(1)
    return match.groups()

def get_transitions(init_digit, target_digit, slot_letter):
    """
    Υπολογίζει ποια σπίρτα πρέπει να αφαιρεθούν (picks) και ποια να προστεθούν (places)
    για να μετατραπεί το init_digit στο target_digit στο συγκεκριμένο slot.
    """
    init_segs = DIGITS_SEGMENTS[init_digit]
    target_segs = DIGITS_SEGMENTS[target_digit]
    
    # Σπίρτα που υπάρχουν στο αρχικό αλλά ΟΧΙ στο τελικό (αφαίρεση)
    picks = [f"{slot_letter}{s}" for s in init_segs if s not in target_segs]
    # Σπίρτα που ΔΕΝ υπάρχουν στο αρχικό αλλά χρειάζονται στο τελικό (προσθήκη)
    places = [f"{slot_letter}{s}" for s in target_segs if s not in init_segs]
    
    return picks, places

def main():
    args = parse_arguments()
    num1, op, num2, num3 = parse_problem(args.problem)
    
    print("\n=== ΕΛΕΓΧΟΣ MILESTONE 2 ===")
    print(f"Ανάλυση μεταβολών για το πρόβλημα: {args.problem}")
    
    # Δοκιμή 1: Μετατροπή του 0 σε 7 στο Slot D (όπως στο παράδειγμα του benchmark σου!)
    d_picks, d_places = get_transitions(0, 7, "D")
    print(f"Μετάβαση 0 -> 7 στο slot D: Picks={d_picks}, Places={d_places}")
    
    # Δοκιμή 2: Μετατροπή του 1 σε 7 στο Slot F
    f_picks, f_places = get_transitions(1, 7, "F")
    print(f"Μετάβαση 1 -> 7 στο slot F: Picks={f_picks}, Places={f_places}")
    print("===========================\n")

if __name__ == "__main__":
    main()
