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

# Εδώ ορίζω πώς ανάβουν τα σπίρτα (0-6) για κάθε ψηφίο από το 0 έως το 9
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
    # Διαβάζω τα ορίσματα (--problem και --max-k) που δίνω από το τερματικό
    parser = argparse.ArgumentParser(description="MathStick Puzzle Solver")
    parser.add_argument("--problem", type=str, required=True, help="Η εξίσωση (π.χ. '0+0=1')")
    parser.add_argument("--max-k", type=int, default=2, help="Μέγιστο πλήθος κινήσεων")
    return parser.parse_args()

def parse_problem(problem_str):
    # Καθαρίζω τυχόν κενά διαστήματα που μπορεί να έβαλε ο χρήστης
    clean_str = re.sub(r'\s+', '', problem_str)
    
    # Σπάω την εξίσωση στα 4 βασικά της μέρη χρησιμοποιώντας Regular Expressions
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
    
    # Φτιάχνω μια λίστα με όλα τα αρχικά ψηφία και τους δίνω γράμματα-slots (A, B, C...)
    initial_digits = [int(c) for c in num1_str + num2_str + num3_str]
    num_slots = len(initial_digits)
    slot_letters = [chr(65 + i) for i in range(num_slots)]
    
    # Κρατάω τα μήκη των αριθμών για να μπορώ να ξαναφτιάξω σωστά το string της εξίσωσης μετά
    len1 = len(num1_str)
    len2 = len(num2_str)

    # Αρχικοποιώ τους μετρητές μου για τους κόμβους που επισκέπτομαι και αυτούς που κλαδεύω
    global_stats = {"visited": 0, "pruned": 0}
    
    # Εδώ θα αποθηκεύω τις λύσεις που βρίσκω ανάλογα με το k (π.χ. "1", "2")
    collected_solutions = {str(k): [] for k in range(1, max_k + 1)}
    seen_solutions = set()

    # Κάνω δύο περάσματα: ένα για την περίπτωση που ο τελεστής-στόχος είναι '+' και ένα για '-'
    for target_op in ["+", "-"]:
        base_picks = []
        base_places = []
        
        # Ελέγχω αν αλλάζει ο κεντρικός τελεστής (το σπίρτο G0)
        if initial_op == "+" and target_op == "-":
            base_picks.append("G0")
        elif initial_op == "-" and target_op == "+":
            base_places.append("G0")

        def dfs(slot_idx, current_picks, current_places):
            # Κάθε φορά που μπαίνω στη συνάρτηση, αυξάνω τους επισκεπτόμενους κόμβους
            global_stats["visited"] += 1

            # Αν έφτασα στο τέλος (δηλαδή βρήκα ψηφία για όλα τα slots)
            if slot_idx == num_slots:
                # Πρέπει τα σπίρτα που έβγαλα να είναι ίσα με αυτά που έβαλα, και να έχω κάνει τουλάχιστον 1 κίνηση
                if len(current_picks) != len(current_places) or len(current_picks) == 0:
                    global_stats["pruned"] += 1
                    return
                
                k_str = str(len(current_picks))
                if k_str not in collected_solutions:
                    global_stats["pruned"] += 1
                    return

                # Φτιάχνω το string των νέων αριθμών με βάση τις επιλογές που έκανα
                decoded_str = "".join(str(d) for d in chosen_digits)
                n1 = int(decoded_str[:len1])
                n2 = int(decoded_str[len1:len1+len2])
                n3 = int(decoded_str[len1+len2:])
                
                # Ελέγχω αν η νέα εξίσωση βγαίνει σωστή μαθηματικά
                is_correct = (n1 + n2 == n3) if target_op == "+" else (n1 - n2 == n3)
                
                if is_correct:
                    eq_formatted = f"{decoded_str[:len1]} {target_op} {decoded_str[len1:len1+len2]} = {decoded_str[len1+len2:]}"
                    
                    # Ταξινομώ αλφαβητικά τα picks και τα places (όπως ζητάει η εκφώνηση)
                    sorted_picks = sorted(current_picks)
                    sorted_places = sorted(current_places)
                    
                    # Ενώνω τα ταξινομημένα στοιχεία ένα-προς-ένα για να φτιάξω τα Moves
                    moves = [f"Move({p}, {pl})" for p, pl in zip(sorted_picks, sorted_places)]
                    sol_key = (eq_formatted, tuple(moves))
                    
                    # Αν δεν έχω ξαναδεί αυτή τη λύση, την αποθηκεύω
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

            # Δοκιμάζω όλα τα πιθανά ψηφία (0-9) για το τρέχον slot
            letter = slot_letters[slot_idx]
            init_segs = DIGITS_SEGMENTS[initial_digits[slot_idx]]
            
            for d in range(10):
                target_segs = DIGITS_SEGMENTS[d]
                
                # Βρίσκω ποια σπίρτα αφαιρούνται και ποια μπαίνουν για να γίνει η αλλαγή στο slot
                slot_picks = [f"{letter}{s}" for s in init_segs if s not in target_segs]
                slot_places = [f"{letter}{s}" for s in target_segs if s not in init_segs]
                
                next_picks = current_picks + slot_picks
                next_places = current_places + slot_places
                
                # LOOK-AHEAD PRUNING: Ελέγχω αν βγαίνω εκτός budget ΠΡΙΝ καλέσω αναδρομικά τον εαυτό μου
                if len(next_picks) <= max_k and len(next_places) <= max_k:
                    chosen_digits.append(d)
                    dfs(slot_idx + 1, next_picks, next_places)
                    chosen_digits.pop() # Backtracking: βγάζω το ψηφίο για να δοκιμάσω το επόμενο
                else:
                    # Αν ξεπερνάει το όριο, το κλαδεύω αμέσως χωρίς να χάνω χρόνο
                    global_stats["pruned"] += 1

        chosen_digits = []
        # Ξεκινάω τον DFS μόνο αν η αρχική κατάσταση του τελεστή δεν κλέβει ήδη όλο το budget μας
        if len(base_picks) <= max_k and len(base_places) <= max_k:
            dfs(0, base_picks, base_places)
        else:
            global_stats["pruned"] += 1

    # Ταξινομώ τις λύσεις αλφαβητικά για να είμαι 100% σίγουρος ότι θα ταιριάζουν με τον autograder
    for k_str in collected_solutions:
        collected_solutions[k_str].sort(key=lambda x: (x["equation"], x["moves"]))

    # Μαζεύω όλα τα δεδομένα στην τελική δομή JSON
    output_data = {
        "problem": problem_str,
        "max_k": max_k,
        "counts": {k: len(v) for k, v in collected_solutions.items()},
        "nodes_visited": global_stats["visited"],
        "nodes_pruned": global_stats["pruned"],
        "solutions": collected_solutions
    }

    # Εκτυπώνω το τελικό αποτέλεσμα στην οθόνη με όμορφη στοίχιση
    print(json.dumps(output_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
