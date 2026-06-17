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

# Αναπαράσταση ψηφίων σε 7-segment display (0-9)
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
    parser = argparse.ArgumentParser(description="MathStick Puzzle Solver")
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

def main():
    args = parse_arguments()
    problem_str = args.problem
    max_k = args.max_k

    num1_str, initial_op, num2_str, num3_str = parse_problem(problem_str)
    
    # Δημιουργία των slots ψηφίων (A, B, C...) από αριστερά προς τα δεξιά
    initial_digits = [int(c) for c in num1_str + num2_str + num3_str]
    num_slots = len(initial_digits)
    slot_letters = [chr(65 + i) for i in range(num_slots)]
    
    len1 = len(num1_str)
    len2 = len(num2_str)

    # Καθολικοί μετρητές για την αναζήτηση (DFS)
    global_stats = {"visited": 0, "pruned": 0}
    
    # Αποθήκευση λύσεων ανά k (από 1 έως max_k)
    collected_solutions = {str(k): [] for k in range(1, max_k + 1)}
    seen_solutions = set()

    # Δύο περάσματα: ένα για target_op='+' και ένα για target_op='-'
    for target_op in ["+", "-"]:
        base_picks = []
        base_places = []
        
        # Έλεγχος αν αλλάζει ο κεντρικός τελεστής (σπίρτο G0)
        if initial_op == "+" and target_op == "-":
            base_picks.append("G0")
        elif initial_op == "-" and target_op == "+":
            base_places.append("G0")

        def dfs(slot_idx, current_picks, current_places):
            global_stats["visited"] += 1

            # Φτάσαμε σε φύλλο (έχουμε επιλέξει ψηφία για όλα τα slots)
            if slot_idx == num_slots:
                # Πρέπει ο αριθμός των picks να ισούται με τα places και να έχουμε κάνει τουλάχιστον 1 κίνηση
                if len(current_picks) != len(current_places) or len(current_picks) == 0:
                    global_stats["pruned"] += 1
                    return
                
                k_str = str(len(current_picks))
                if k_str not in collected_solutions:
                    global_stats["pruned"] += 1
                    return

                # Ανασύσταση της εξίσωσης
                decoded_str = "".join(str(d) for d in chosen_digits)
                n1 = int(decoded_str[:len1])
                n2 = int(decoded_str[len1:len1+len2])
                n3 = int(decoded_str[len1+len2:])
                
                # Μαθηματικός έλεγχος ορθότητας
                is_correct = (n1 + n2 == n3) if target_op == "+" else (n1 - n2 == n3)
                
                if is_correct:
                    eq_formatted = f"{decoded_str[:len1]} {target_op} {decoded_str[len1:len1+len2]} = {decoded_str[len1+len2:]}"
                    
                    # Ντετερμινιστικό Sort-and-Zip
                    sorted_picks = sorted(current_picks)
                    sorted_places = sorted(current_places)
                    
                    # Δημιουργία των Moves μορφής Move(src, dst)
                    moves = [f"Move({p}, {pl})" for p, pl in zip(sorted_picks, sorted_places)]
                    sol_key = (eq_formatted, tuple(moves))
                    
                    if sol_key not in seen_solutions:
                        seen_solutions.add(sol_key)
                        collected_solutions[k_str].append({
                            "equation": eq_formatted,
                            "picks": sorted_picks,
                            "places": sorted_places,
                            "moves": moves,
                            "nodes_visited": global_stats["visited"],
                            "nodes_pruned": global_stats["pruned"]
                        })
                else:
                    global_stats["pruned"] += 1
                return

            # Δοκιμή όλων των ψηφίων 0-9 για το τρέχον slot
            letter = slot_letters[slot_idx]
            init_segs = DIGITS_SEGMENTS[initial_digits[slot_idx]]
            
            for d in range(10):
                target_segs = DIGITS_SEGMENTS[d]
                
                # Υπολογισμός picks/places για το συγκεκριμένο slot
                slot_picks = [f"{letter}{s}" for s in init_segs if s not in target_segs]
                slot_places = [f"{letter}{s}" for s in target_segs if s not in init_segs]
                
                next_picks = current_picks + slot_picks
                next_places = current_places + slot_places
                
                # LOOK-AHEAD PRUNING: Έλεγχος ΠΡΙΝ την αναδρομική κλήση
                if len(next_picks) <= max_k and len(next_places) <= max_k:
                    chosen_digits.append(d)
                    dfs(slot_idx + 1, next_picks, next_places)
                    chosen_digits.pop()
                else:
                    # Αν οι κινήσεις ξεπερνούν το όριο, το κλαδεύουμε άμεσα
                    global_stats["pruned"] += 1

        chosen_digits = []
        # Ξεκινάμε την αναζήτηση μόνο αν η αρχική κατάσταση του τελεστή δεν παραβιάζει το max_k
        if len(base_picks) <= max_k and len(base_places) <= max_k:
            dfs(0, base_picks, base_places)
        else:
            global_stats["pruned"] += 1

    # Τελική δομή εξόδου
    output_data = {
        "problem": problem_str,
        "max_k": max_k,
        "counts": {k: len(v) for k, v in collected_solutions.items()},
        "nodes_visited": global_stats["visited"],
        "nodes_pruned": global_stats["pruned"],
        "solutions": collected_solutions
    }

    print(json.dumps(output_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
