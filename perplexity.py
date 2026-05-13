import argparse
import sys
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate Perplexity using GPT-2 with a sliding window.")
    parser.add_argument("--n-ctx", type=int, default=2048, help="Μέγεθος παραθύρου (context window).")
    parser.add_argument("--stride", type=int, default=512, help="Βήμα μετατόπισης (stride).")
    parser.add_argument("--begin-context-tokens", type=int, default=512, help="Αρχικά tokens (warmup context).")
    parser.add_argument("input_file", type=str, help="Το αρχείο κειμένου εισόδου (.txt)")
    parser.add_argument("output_file", type=str, help="Το αρχείο αποτελεσμάτων (.out)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Επιλογή κάρτας γραφικών ή επεξεργαστή
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "gpt2"

    print(f"Computing perplexity for {args.input_file}...")
    
    # Φόρτωση του μοντέλου και του tokenizer
    try:
        model = GPT2LMHeadModel.from_pretrained(model_id).to(device)
        tokenizer = GPT2Tokenizer.from_pretrained(model_id)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    # Ανάγνωση αρχείου
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Το αρχείο '{args.input_file}' δεν βρέθηκε.")
        sys.exit(1)

    print("Tokenizing text...")
    encodings = tokenizer(text, return_tensors="pt")
    input_ids = encodings.input_ids.to(device)
    
    total_len = input_ids.size(1)
    print(f"Found {total_len} tokens.")

    # --- Υπολογισμός Sliding Window ---
    n_ctx = args.n_ctx
    stride = args.stride
    begin_tokens = args.begin_context_tokens

    nlls = [] # Λίστα για τα αρνητικά λογαριθμοπίθανα
    prev_end = 0
    window_count = 1

    # Υπολογισμός συνολικών παραθύρων για το print
    total_windows = (total_len - begin_tokens + stride - 1) // stride + 1
    print(f"Processing {total_len} tokens in {total_windows} window(s).")

    for begin_loc in range(0, total_len, stride):
        end_loc = min(begin_loc + n_ctx, total_len)
        
        # Πόσα tokens θα βαθμολογήσουμε σε αυτό το παράθυρο;
        if begin_loc == 0:
            trg_len = end_loc # Στο πρώτο παράθυρο τα βαθμολογούμε όλα
        else:
            trg_len = end_loc - prev_end # Στα επόμενα μόνο τα "νέα" tokens
            
        input_ids_window = input_ids[:, begin_loc:end_loc]
        target_ids = input_ids_window.clone()
        
        # Αφήνουμε εκτός υπολογισμού τα tokens που αποτελούν το "παρελθόν" (context)
        target_ids[:, :-trg_len] = -100

        with torch.no_grad():
            outputs = model(input_ids_window, labels=target_ids)
            # Το loss είναι το μέσο NLL, οπότε πολλαπλασιάζουμε με το μήκος στόχου
            neg_log_likelihood = outputs.loss * trg_len

        nlls.append(neg_log_likelihood)
        print(f"Window {window_count}/{total_windows}: nll={neg_log_likelihood.item():.4f}")
        
        window_count += 1
        prev_end = end_loc
        if end_loc == total_len:
            break

    # Τελικός υπολογισμός Perplexity
    perplexity = torch.exp(torch.stack(nlls).sum() / total_len)
    
    # Εγγραφή στο αρχείο εξόδου
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(f"Perplexity: {perplexity.item():.2f}\n")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        
    print(f"Final Perplexity: {perplexity.item():.2f}")

# --- Ο Διακόπτης Εκκίνησης ---
if __name__ == "__main__":
    main()