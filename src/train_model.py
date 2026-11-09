"""Train XGBoost resistance classifier using ESM-2 Delta Embeddings."""

import argparse
from pathlib import Path
import numpy as np
import torch
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from transformers import AutoModel, AutoTokenizer

from .load_data import load_csv
from .validate_data import validate_rows


def extract_coordinate_embedding(sequence: str, mutation_idx: int, tokenizer, model, device) -> np.ndarray:
    """Extracts the ESM-2 hidden state vector at a specific 0-indexed mutation coordinate."""
    if not sequence:
        return np.zeros(model.config.hidden_size)
    
    inputs = tokenizer(sequence, return_tensors="pt", add_special_tokens=True, truncation=True, max_length=1024)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    # last_hidden_state shape: (batch_size, sequence_length, embedding_dim)
    # Tokenizer adds [CLS] at index 0, so residue i is at index i + 1
    token_embeddings = outputs.last_hidden_state[0]
    target_token_idx = mutation_idx + 1
    
    if target_token_idx >= token_embeddings.shape[0]:
        raise ValueError(f"Mutation index {mutation_idx} is out of bounds for sequence length {len(sequence)}.")
        
    return token_embeddings[target_token_idx].cpu().numpy()


def build_delta_dataset(rows, model_name="facebook/esm2_t6_8M_UR50D"):
    """Builds feature matrix using the Delta Embedding Method: Mutant - Wildtype."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading ESM-2 model ({model_name}) on {device.upper()}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    X, y = [], []
    print("Computing Delta Embeddings across variants...")

    for row in rows:
        wt_seq = row.get("protein_sequence", "").strip()
        mut_seq = row.get("mutant_seq", "").strip()
        label_str = row.get("resistance_label", "").strip()
        
        # Skip incomplete rows
        if not wt_seq or not mut_seq or not label_str:
            continue
            
        try:
            mut_idx = int(row.get("mutation_idx", 0))
        except ValueError:
            continue

        # 1. Extract wild-type vector at coordinate
        wt_vec = extract_coordinate_embedding(wt_seq, mut_idx, tokenizer, model, device)
        
        # 2. Extract mutant vector at coordinate
        mut_vec = extract_coordinate_embedding(mut_seq, mut_idx, tokenizer, model, device)
        
        # 3. Calculate Delta Vector (structural/chemical shift)
        delta_vec = mut_vec - wt_vec
        
        X.append(delta_vec)
        y.append(int(label_str))

    return np.array(X), np.array(y)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to validated resistance CSV")
    parser.add_argument("--model-name", default="facebook/esm2_t6_8M_UR50D", help="Hugging Face ESM-2 checkpoint")
    parser.add_argument("--output-model", default="models/xgboost_kpc.json", help="Path to save trained XGBoost model")
    args = parser.parse_args()

    # Step 1: Ingest and Validate using your existing repository modules
    print(f"Loading and validating {args.input}...")
    rows = load_csv(args.input)
    errors = validate_rows(rows)
    if errors:
        raise ValueError("Data validation failed:\n" + "\n".join(errors))

    # Step 2: Build Delta Feature Matrix
    X, y = build_delta_dataset(rows, model_name=args.model_name)
    
    if len(np.unique(y)) < 2:
        raise ValueError("Training dataset must contain both resistant (1) and sensitive (0) labels.")

    print(f"Feature matrix built successfully! Shape: {X.shape}")

    # Step 3: Train/Test Split & XGBoost Classification
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training XGBoost Classifier...")
    clf = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
    clf.fit(X_train, y_train)

    # Step 4: Evaluate Performance
    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, preds)
    try:
        auc = roc_auc_score(y_test, probs)
    except ValueError:
        auc = float("nan")

    print(f"\n--- Model Evaluation ---")
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test ROC-AUC:  {auc:.4f}")

    # Step 5: Save Model Artifact
    output_path = Path(args.output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clf.save_model(output_path)
    print(f"Trained model saved to {output_path}")


if __name__ == "__main__":
    main()
