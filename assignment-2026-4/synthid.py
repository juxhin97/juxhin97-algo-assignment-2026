# ==========================================================
# Εργασία Αλγορίθμων 2026 
# Παραδοτέο 4: Υδατογράφηση Κειμένου (SynthID-Text)
# Όνομα: Γιουτζίν Τσάτσα (Juxhin Caca)
# ΑΜ: 8150141
# ==========================================================

import sys
import json
import math
import hashlib
from typing import List, Dict, Any, Tuple, Set

# Εισαγωγή του δοθέντος toolkit
import toolkit

def sample_layered(p: List[float], g: Any, m: int) -> List[float]:
    """
    Υπολογίζω τη διαστρωματωμένη (layered) κατανομή πιθανοτήτων
    μετά από m επίπεδα τουρνουά.
    """
    current_p = list(p)
    num_tokens = len(current_p)

    for layer in range(m):
        # Υπολογίζω το qA (άθροισμα πιθανοτήτων για τα τεμάχια με g=0)
        q_A = 0.0
        for i in range(num_tokens):
            g_val = g(i, layer) if callable(g) else g[layer][i]
            if g_val == 0:
                q_A += current_p[i]

        # Ενημερώνω τις πιθανότητες για το τρέχον επίπεδο
        for i in range(num_tokens):
            g_val = g(i, layer) if callable(g) else g[layer][i]
            if g_val == 0:
                current_p[i] = current_p[i] * q_A
            else:
                current_p[i] = current_p[i] * (q_A + 1.0)

    return current_p

def sample_knockout(p: List[float], g: Any, m: int, rng: Any) -> int:
    """
    Θα υλοποιηθεί στο επόμενο βήμα.
    """
    pass

def generate(args):
    pass

def detect(args):
    pass

if __name__ == "__main__":
    toolkit.run(generate, detect)
  
