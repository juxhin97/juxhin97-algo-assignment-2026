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

# Βοηθητική συνάρτηση για ασφαλή μετατροπή δομών σε hashable
def make_hashable(obj):
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(x) for x in obj)
    if isinstance(obj, (set, frozenset)):
        try:
            return tuple(sorted(make_hashable(x) for x in obj))
        except Exception:
            return tuple(sorted(str(make_hashable(x)) for x in obj))
    try:
        hash(obj)
        return obj
    except Exception:
        return str(obj)

# ==========================================================
# ΤΜΗΜΑ Α: Δειγματοληψία (Samplers) & Παραγωγή Κειμένου
# ==========================================================

def sample_layered(p, g, m):
    current_p = list(p)
    num_tokens = len(current_p)

    for layer in range(m):
        q_A = 0.0
        for i in range(num_tokens):
            g_val = g(i, layer) if callable(g) else g[layer][i]
            if g_val == 0:
                q_A += current_p[i]

        for i in range(num_tokens):
            g_val = g(i, layer) if callable(g) else g[layer][i]
            if g_val == 0:
                current_p[i] = current_p[i] * q_A
            else:
                current_p[i] = current_p[i] * (q_A + 1.0)

        tolerance = max(1e-9, (2 ** m) * 1e-15)
        assert abs(sum(current_p) - 1.0) < tolerance, "Σφάλμα: Το άθροισμα διαφέρει από το 1"

    return current_p

def sample_knockout(p, g, m, rng):
    num_candidates = 1 << m
    candidates = []
    
    for _ in range(num_candidates):
        idx = toolkit.choose(p, rng.random())
        candidates.append(idx)
    
    for layer in range(m):
        next_round = []
        for i in range(0, len(candidates), 2):
            left = candidates[i]
            right = candidates[i + 1]
            
            g_left = g(left, layer) if callable(g) else g[layer][left]
            g_right = g(right, layer) if callable(g) else g[layer][right]
            
            if g_left >= g_right:
                next_round.append(left)
            else:
                next_round.append(right)
        candidates = next_round
        
    return candidates[0]

def generate(*pos_args, **kwargs):
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
    
    prompt_len = min(window, length)
    for _ in range(prompt_len):
        token_idx = rng.randrange(toolkit.VOCAB_SIZE)
        tokens.append(toolkit.TOKENS[token_idx])
        
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
# ΤΜΗΜΑ Β: Βαθμολόγηση (Scoring) & Φίλτρο Bloom
# ==========================================================

def scored_positions(tokens, h):
    seen = set()
    scorable = set()
    if not tokens or len(tokens) < h:
        return scorable
    for t in range(h, len(tokens)):
        ctx = make_hashable(context_item(tokens[t-h:t]))
        if ctx not in seen:
            seen.add(ctx)
            scorable.add(t)
    return scorable

def score_numerator(tokens, key, h, m):
    pos = scored_positions(tokens, h)
    total = 0
    for t in pos:
        ctx = tokens[t-h:t]
        tok = tokens[t]
        for layer in range(m):
            total += g_value(key, ctx, layer, tok)
    return total

def mean_score(tokens, key, h, m):
    pos = scored_positions(tokens, h)
    if not pos:
        return 0.0
    num = score_numerator(tokens, key, h, m)
    return num / (m * len(pos))

class BloomFilter:
    def __init__(self, nbits, k):
        self.nbits = nbits
        self.k = k
        self.bits = bytearray((nbits + 7) // 8)

    def add(self, item):
        item_str = str(make_hashable(item))
        bit_positions = bloom_hash_positions(item_str, self.nbits, self.k)
        for bit in bit_positions:
            self.bits[bit >> 3] |= (1 << (bit & 7))

    def contains(self, item):
        item_str = str(make_hashable(item))
        bit_positions = bloom_hash_positions(item_str, self.nbits, self.k)
        return all((self.bits[bit >> 3] & (1 << (bit & 7))) != 0 for bit in bit_positions)

def bloom_scored_positions(tokens, h, nbits, k):
    exact_seen = set()
    bloom = BloomFilter(nbits, k)
    scorable = set()
    false_skips = 0

    if not tokens or len(tokens) < h:
        return scorable, false_skips

    for t in range(h, len(tokens)):
        raw_ctx = context_item(tokens[t-h:t])
        ctx = make_hashable(raw_ctx)
        exact_has = (ctx in exact_seen)
        bloom_has = bloom.contains(raw_ctx)

        if not bloom_has:
            scorable.add(t)
            bloom.add(raw_ctx)
            exact_seen.add(ctx)
        else:
            if not exact_has:
                false_skips += 1

    return scorable, false_skips

# ==========================================================
# ΤΜΗΜΑ Γ: Ιστόγραμμα, Όριο & Ανίχνευση (Histogram, Threshold, Detect)
# ==========================================================

def histogram(numerators, length, m):
    max_score = m * length
    if numerators:
        max_score = max(max_score, max(numerators))
    hist = [0] * (max_score + 1)
    for num in numerators:
        if 0 <= num < len(hist):
            hist[num] += 1
    return hist

def threshold(hist, n_docs, alpha):
    if n_docs <= 0:
        return len(hist)
    tail = sum(hist)
    for k in range(len(hist)):
        if (tail / n_docs) <= alpha:
            return k
        tail -= hist[k]
    return len(hist)

def detect(*pos_args, **kwargs):
    args_obj = pos_args[0] if pos_args else None
    
    def get_val(names, default=None):
        if isinstance(names, str):
            names = [names]
        for name in names:
            if kwargs and name in kwargs:
                return kwargs[name]
            if args_obj is not None:
                if isinstance(args_obj, dict) and name in args_obj:
                    return args_obj[name]
                elif hasattr(args_obj, name):
                    return getattr(args_obj, name)
        return default

    key = get_val(['key', 'watermark_key'])
    calibration_source = get_val(['calibration', 'calibrations', 'cal'])
    documents_source = get_val(['documents', 'document', 'docs'])
    alpha = get_val(['alpha'], 0.1)
    window = get_val(['window', 'h'], 4)
    layers = get_val(['layers', 'm'], 30)
    bloom_bits = get_val(['bloom_bits', 'bloom', 'bloom_filter', 'nbits'])
    bloom_k = get_val(['bloom_k', 'k'], 4)

    def load_docs(source):
        docs = []
        if source is None:
            return docs
        if hasattr(source, 'read'):
            for line in source:
                tokens = line.strip().split()
                if tokens:
                    docs.append(tokens)
            return docs
        if isinstance(source, str):
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    for line in f:
                        tokens = line.strip().split()
                        if tokens:
                            docs.append(tokens)
                if docs:
                    return docs
            except Exception:
                pass
            for line in source.strip().splitlines():
                tokens = line.strip().split()
                if tokens:
                    docs.append(tokens)
            if docs:
                return docs
            docs.append(source.strip().split())
            return docs
        elif isinstance(source, (list, tuple)):
            for item in source:
                if isinstance(item, str):
                    tokens = item.strip().split()
                    if tokens:
                        docs.append(tokens)
                elif isinstance(item, (list, tuple)):
                    docs.append(list(item))
        return docs

    cal_docs = load_docs(calibration_source)
    cal_numerators = []
    max_len = 0
    for doc in cal_docs:
        max_len = max(max_len, len(doc))
        if bloom_bits:
            scorable, _ = bloom_scored_positions(doc, window, bloom_bits, bloom_k)
            num = 0
            for t in scorable:
                ctx = doc[t-window:t]
                tok = doc[t]
                for layer in range(layers):
                    num += g_value(key, ctx, layer, tok)
            cal_numerators.append(num)
        else:
            cal_numerators.append(score_numerator(doc, key, window, layers))

    hist = histogram(cal_numerators, max_len, layers)
    thresh = threshold(hist, len(cal_docs), alpha)

    eval_docs = load_docs(documents_source)
    results = []
    for doc in eval_docs:
        if bloom_bits:
            scorable, _ = bloom_scored_positions(doc, window, bloom_bits, bloom_k)
            num = 0
            for t in scorable:
                ctx = doc[t-window:t]
                tok = doc[t]
                for layer in range(layers):
                    num += g_value(key, ctx, layer, tok)
            mean = num / (layers * len(scorable)) if scorable else 0.0
        else:
            num = score_numerator(doc, key, window, layers)
            mean = mean_score(doc, key, window, layers)

        results.append({
            "numerator": num,
            "mean": mean,
            "watermarked": num >= thresh
        })

    return {
        "mode": "detect",
        "key": key,
        "alpha": alpha,
        "threshold": thresh,
        "histogram": hist,
        "results": results,
        "calibration": calibration_source,
        "bloom": bloom_bits
    }

if __name__ == "__main__":
    toolkit.run(generate, detect)
    
