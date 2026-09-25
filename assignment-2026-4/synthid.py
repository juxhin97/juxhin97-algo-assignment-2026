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

# Εισαγωγή των συναρτήσεων από το δοθέν toolkit
import toolkit
from toolkit import context_item, g_value, bloom_hash_positions

# ==========================================================
# ΤΜΗΜΑ Α: Δειγματοληψία (Samplers) & Παραγωγή Κειμένου
# ==========================================================

def sample_layered(p, g, m):
    # Υπολογισμός της layered κατανομής για m επίπεδα
    current_p = list(p)
    num_tokens = len(current_p)

    for layer in range(m):
        # Υπολογίζω το άθροισμα qA για τα στοιχεία με g=0
        q_A = 0.0
        for i in range(num_tokens):
            g_val = g(i, layer) if callable(g) else g[layer][i]
            if g_val == 0:
                q_A += current_p[i]

        # Ενημερώνω τις πιθανότητες για το επόμενο επίπεδο
        for i in range(num_tokens):
            g_val = g(i, layer) if callable(g) else g[layer][i]
            if g_val == 0:
                current_p[i] = current_p[i] * q_A
            else:
                current_p[i] = current_p[i] * (q_A + 1.0)

        # Έλεγχος ανοχής αθροίσματος (πρέπει να ισούται με 1)
        tolerance = max(1e-9, (2 ** m) * 1e-15)
        assert abs(sum(current_p) - 1.0) < tolerance, "Σφάλμα: Το άθροισμα διαφέρει από το 1"

    return current_p

def sample_knockout(p, g, m, rng):
    # Διεξαγωγή τουρνουά knockout 2^m υποψηφίων
    num_candidates = 1 << m
    candidates = []
    
    # Κληρώνω 2^m υποψηφίους από την αρχική κατανομή
    for _ in range(num_candidates):
        idx = toolkit.choose(p, rng.random())
        candidates.append(idx)
    
    # Γύροι τουρνουά
    for layer in range(m):
        next_round = []
        for i in range(0, len(candidates), 2):
            left = candidates[i]
            right = candidates[i + 1]
            
            g_left = g(left, layer) if callable(g) else g[layer][left]
            g_right = g(right, layer) if callable(g) else g[layer][right]
            
            # Σε ισοπαλία (g_left == g_right), προκρίνεται ο αριστερός
            if g_left >= g_right:
                next_round.append(left)
            else:
                next_round.append(right)
        candidates = next_round
        
    return candidates[0]

def generate(*pos_args, **kwargs):
    # Διαχείριση παραμέτρων (είτε από CLI είτε ως arguments)
    if pos_args and hasattr(pos_args[0], 'key'):
        a = pos_args[0]
        key = a.key
        seed = a.seed
        length = a.length
        layers = getattr(a, 'layers', 30)
        window = getattr(a, 'window', 4)
        entropy = getattr(a, 'entropy', 'high')
        sampler = getattr(a, 'sampler', 'layered')
        no_watermark = getattr(a, 'no_watermark', False)
    else:
        key = kwargs.get('key')
        seed = kwargs.get('seed')
        length = kwargs.get('length')
        layers = kwargs.get('layers', 30)
        window = kwargs.get('window', 4)
        entropy = kwargs.get('entropy', 'high')
        sampler = kwargs.get('sampler', 'layered')
        no_watermark = kwargs.get('no_watermark', False)

    rng = toolkit.Randomness("generate", seed)
    model = toolkit.Model(toolkit.MODEL_SEED, toolkit.PROFILES[entropy])
    
    tokens = []
    
    # Δημιουργία αρχικού prompt
    prompt_len = min(window, length)
    for _ in range(prompt_len):
        token_idx = rng.randrange(toolkit.VOCAB_SIZE)
        tokens.append(toolkit.TOKENS[token_idx])
        
    # Παραγωγή των υπολοίπων tokens
    while len(tokens) < length:
        current_window = tokens[-window:]
        dist = model.distribution(current_window)
        
        if no_watermark:
            chosen_local_idx = toolkit.choose(dist.probs, rng.random())
        else:
            def g_func(local_idx, layer):
                tok_str = toolkit.TOKENS[dist.indices[local_idx]]
                return toolkit.g_value(key, current_window, layer, tok_str)
            
            if sampler == "layered":
                new_probs = sample_layered(dist.probs, g_func, layers)
                chosen_local_idx = toolkit.choose(new_probs, rng.random())
            else:
                chosen_local_idx = sample_knockout(dist.probs, g_func, layers, rng)
                
        chosen_token = toolkit.TOKENS[dist.indices[chosen_local_idx]]
        tokens.append(chosen_token)
        
    return {
        "mode": "generate",
        "seed": seed,
        "watermarked": not no_watermark,
        "entropy": entropy,
        "layers": layers,
        "window": window,
        "sampler": sampler,
        "tokens": tokens
    }

# ==========================================================
# ΤΜΗΜΑ Β & Γ: Σκελετοί (Placeholders για επόμενο commit)
# ==========================================================

def scored_positions(tokens, h):
    raise NotImplementedError

def score_numerator(tokens, key, h, m):
    raise NotImplementedError

def mean_score(tokens, key, h, m):
    raise NotImplementedError

class BloomFilter:
    def __init__(self, nbits, k):
        self.nbits = nbits
        self.k = k

    def add(self, item):
        raise NotImplementedError

    def contains(self, item):
        raise NotImplementedError

def bloom_scored_positions(tokens, h, nbits, k):
    raise NotImplementedError

def histogram(numerators, length, m):
    raise NotImplementedError

def threshold(hist, n_docs, alpha):
    raise NotImplementedError

def detect(*args, **kwargs):
    raise NotImplementedError

if __name__ == "__main__":
    toolkit.run(generate, detect)
    
