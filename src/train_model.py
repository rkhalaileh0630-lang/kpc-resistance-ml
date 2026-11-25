"""Train XGBoost resistance classifier using ESM-2 Delta Embeddings on the 9-column schema."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from transformers import AutoModel, AutoTokenizer

from .load_data import load_csv
from .validate_data import validate_rows


def get_token_embeddings(sequence: str, tokenizer, model, device) -> np.ndarray:
    """Return per-token hidden states of shape (num_tokens, hidden_dim)."""
    inputs = tokenizer(
        sequence,
        return_tensors="pt",
        add_special_tokens=True,
        truncation=True,
        max_length=1024,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[0].cpu().numpy()


def resolve_wildtype_sequence(rows, wt_variant: str, wt_sequence_arg: str | None) -> str:
    """Resolve reference wildtype protein sequence from CLI or matching variant_id."""
    if wt_sequence_arg:
        return wt_sequence_arg.strip().upper()
    for row in rows:
        if row["variant_id"].strip() == wt_variant and row["protein_sequence"].strip():
            return row["protein_sequence"].strip().upper()
    raise ValueError(
        f"Could not find non-empty protein_sequence for variant_id '{wt_variant}'. "
        "Pass --wt-sequence or ensure the wildtype row is present."
    )


def build_delta_dataset(rows, wt_seq: str, model_name: str):
    """Build feature matrix (X) and binary labels (y) from coordinate deltas vs. wildtype."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading ESM-2 model ({model_name}) on {device.upper()}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    wt_tokens = get_token_embeddings(wt_seq, tokenizer, model, device)
    max_seq_tokens = wt_tokens.shape[0] - 2

    X, y = [], []
    skipped = 0

    for row in rows:
        mut_seq = row["protein_sequence"].strip().upper()
        label_str = row["resistance_label"].strip()
        if not mut_seq or label_str not in ("0", "1"):
            skipped += 1
            continue
        if len(mut_seq) != len(wt_seq):
            skipped += 1
            continue

        mut_positions = [
            idx for idx, (w_aa, m_aa) in enumerate(zip(wt_seq, mut_seq))
            if w_aa != m_aa and idx < max_seq_tokens
        ]
        if not mut_positions:
            X.append(np.zeros(wt_tokens.shape[1], dtype=np.float32))
            y.append(int(label_str))
            continue

        mut_tokens = get_token_embeddings(mut_seq, tokenizer, model, device)
        deltas = [mut_tokens[pos + 1] - wt_tokens[pos + 1] for pos in mut_positions]
        X.append(np.mean(deltas, axis=0).astype(np.float32))
        y.append(int(label_str))

    print(f"Usable labeled rows: {len(y)} (skipped {skipped} incomplete/mismatched/unlabeled rows).")
    return np.array(X), np.array(y)


def log_run(log_path: Path, record: dict):
    """Append training session metrics to a CSV log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(record.keys())
    write_header = not log_path.exists()
    with log_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to 9-column KPC CSV")
    parser.add_argument("--wt-variant", default="KPC-2", help="variant_id of wildtype reference row")
    parser.add_argument("--wt-sequence", default=None, help="Explicit wildtype sequence override")
    parser.add_argument("--model-name", default="facebook/esm2_t6_8M_UR50D", help="Hugging Face ESM-2 checkpoint")
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-model", default="models/xgboost_kpc.json")
    parser.add_argument("--log-file", default="reports/training_runs.csv")
    args = parser.parse_args()

    rows = load_csv(args.input)
    errors = validate_rows(rows)
    if errors:
        raise ValueError("Data validation failed:\n" + "\n".join(errors))

    wt_seq = resolve_wildtype_sequence(rows, args.wt_variant, args.wt_sequence)
    X, y = build_delta_dataset(rows, wt_seq=wt_seq, model_name=args.model_name)

    if len(y) < 2 or len(np.unique(y)) < 2:
        raise ValueError("Need at least 2 usable rows containing both class 0 and class 1.")

    stratify = y if np.min(np.bincount(y)) >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=stratify
    )

    clf = xgb.XGBClassifier(
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
        eval_metric="logloss",
        random_state=args.seed,
    )
    clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    acc = float(accuracy_score(y_test, preds))
    try:
        auc = float(roc_auc_score(y_test, probs))
    except ValueError:
        auc = float("nan")

    output_path = Path(args.output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clf.save_model(output_path)

    log_path = Path(args.log_file)
    log_run(
        log_path,
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "input_csv": str(args.input),
            "model_name": args.model_name,
            "samples_used": len(y),
            "n_estimators": args.n_estimators,
            "learning_rate": args.learning_rate,
            "max_depth": args.max_depth,
            "seed": args.seed,
            "test_accuracy": round(acc, 4),
            "test_roc_auc": round(auc, 4) if not np.isnan(auc) else "",
            "model_path": str(output_path),
        },
    )

    print("\n--- Model Evaluation ---")
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test ROC-AUC:  {auc:.4f}")
    print(f"Model saved to: {output_path}")
    print(f"Run logged to:  {log_path}")


if __name__ == "__main__":
    main()
