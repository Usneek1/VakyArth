"""XCOMET evaluation for translation task outputs.

This script evaluates model translation outputs using XCOMET, a reference-based
evaluation metric for machine translation from Unbabel.

Paper: https://arxiv.org/pdf/2310.10482
Model: Unbabel/xcomet

Usage:
  python evaluate_with_xcomet.py --language Punjabi
  python evaluate_with_xcomet.py --language all
  python evaluate_with_xcomet.py --language Hindi --category Diexis
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from comet import download_model, load_from_checkpoint

def parse_args():
    parser = argparse.ArgumentParser(
        description="XCOMET evaluation of translation outputs"
    )
    parser.add_argument("--outputs_root", type=Path, default=Path("../outputs"),
                        help="Root directory containing language output folders")
    parser.add_argument("--data_root", type=Path, default=Path("../data"),
                        help="Root directory containing gold translation data")
    parser.add_argument("--language", required=True,
                        help="Language folder name (e.g. Punjabi, Hindi) or 'all'")
    parser.add_argument("--category",
                        help="Optional: filter by category folder name")
    parser.add_argument("--model_name",
                        help="Optional: filter by model_name field in JSONL")
    parser.add_argument("--prompt_style",
                        help="Optional: filter by prompt_style field in JSONL")
    parser.add_argument("--xcomet_model", default="Unbabel/xcomet-xl",
                        help="XCOMET model identifier on Hugging Face")
    parser.add_argument("--max_examples", type=int,
                        help="Limit number of examples per file (for quick tests)")
    parser.add_argument("--batch_size", type=int, default=8,
                        help="Batch size for XCOMET inference")
    parser.add_argument("--device", default="cuda" if __import__("torch").cuda.is_available() else "cpu",
                        help="Device for inference (cuda or cpu)")
    return parser.parse_args()


def load_xcomet_model(model_name: str, device: str):
    print(f"[xcomet] Loading model: {model_name}")
    model_path = download_model(model_name)  # needs unbabel-comet >= 2.2.0
    model = load_from_checkpoint(model_path)
    print("Reached here 1")
    if device == "cuda":
        model = model.cuda()
    print("Reached here 2")
    model.eval()
    print(f"[xcomet] Model loaded on {device}")
    return model


def load_translation_dataset(data_root: Path, language: str, category: str) -> Dict[str, dict]:
    """Return id -> item mapping for the gold translation file."""
    path = data_root / language / category / "translation.json"
    if not path.exists():
        print(f"[warning] Gold file not found: {path}")
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    return {item["id"]: item for item in items if "id" in item}


def prepare_xcomet_data(
    result_file: Path,
    gold_by_id: Dict[str, dict],
    max_examples: Optional[int]
) -> Tuple[List[dict], List[dict]]:
    """Prepare data in XCOMET format and return (xcomet_data, original_records)."""
    records = []
    with result_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    if max_examples:
        records = records[:max_examples]

    xcomet_data = []
    valid_original_records = []

    for rec in records:
        ex_id = rec.get("id", "")
        prediction = rec.get("prediction", {})
        hypothesis = prediction.get("text", "").strip()
        # Reference can come from the record itself or from gold data
        reference = prediction.get("reference", "")

        # Try to get reference from gold dataset if not in prediction
        gold_item = gold_by_id.get(ex_id, {})
        if not reference and gold_item:
            reference = gold_item.get("reference_translation", {}).get("text", "")

        source = ""

        if gold_item:
            source_field = gold_item.get("source", "")

            if isinstance(source_field, dict):
                scripts = source_field.get("scripts", "")
                if isinstance(scripts, dict):
                    latin = scripts.get("latin", "")
                    if isinstance(latin, dict):
                        source = latin.get("source", "")

            elif isinstance(source_field, str):
                source = source_field

        if not hypothesis:
            print(f"[warning] Empty hypothesis for {ex_id}, skipping")
            continue
        if not reference:
            print(f"[warning] No reference for {ex_id}, skipping")
            continue

        xcomet_data.append({
            "src": source,
            "mt": hypothesis,
            "ref": reference
        })
        valid_original_records.append(rec)

    return xcomet_data, valid_original_records


def run_xcomet_evaluation(model, xcomet_data, batch_size):
    if not xcomet_data:
        return [], 0.0
    print(f"[xcomet] Evaluating {len(xcomet_data)} examples with batch_size={batch_size}")
    gpus = 1 if str(next(model.parameters()).device) != "cpu" else 0
    # num_workers=1 works around a comet bug on Apple Silicon (see evaluate_translation_comet.py)
    output = model.predict(xcomet_data, batch_size=batch_size, gpus=gpus, num_workers=1)
    return output.scores, output.system_score


def aggregate_statistics(seg_scores: List[float]) -> Dict:
    """Compute statistics from segment-level scores."""
    if not seg_scores:
        return {
            "num_examples": 0,
            "num_scored": 0,
            "coverage": 0.0,
            "avg_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "std_score": 0.0,
        }

    import numpy as np
    scores = np.array(seg_scores)

    return {
        "num_examples": len(scores),
        "num_scored": len(scores),
        "coverage": 1.0,
        "avg_score": float(np.mean(scores)),
        "min_score": float(np.min(scores)),
        "max_score": float(np.max(scores)),
        "std_score": float(np.std(scores)),
        "median_score": float(np.median(scores)),
        "q25_score": float(np.percentile(scores, 25)),
        "q75_score": float(np.percentile(scores, 75)),
    }


def main():
    args = parse_args()

    # Determine languages to process
    if args.language.lower() == "all":
        languages = [d.name for d in args.outputs_root.iterdir() if d.is_dir()]
    else:
        languages = [args.language]

    # Load XCOMET model
    model = load_xcomet_model(args.xcomet_model, args.device)

    all_metrics = []

    for language in languages:
        lang_dir = args.outputs_root / language
        if not lang_dir.exists():
            print(f"No outputs found for language: {language}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing language: {language}")
        print(f"{'='*60}")

        # Iterate through categories (coherence, Diexis, Implicature, etc.)
        for cat_dir in sorted(lang_dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            category = cat_dir.name
            if args.category and category != args.category:
                continue

            # Translation task
            task_dir = cat_dir / "translation"
            if not task_dir.exists():
                print(f"  [skip] No translation folder in {category}")
                continue

            # Process each JSONL file
            for result_file in sorted(task_dir.glob("*.jsonl")):
                # Skip already judged files if they exist
                if result_file.name.endswith(".judged.jsonl"):
                    continue

                # Peek at first record for model_name / prompt_style
                first_rec = None
                try:
                    with result_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                first_rec = json.loads(line)
                                break
                except Exception as e:
                    print(f"  [error] Could not read {result_file.name}: {e}")
                    continue

                if first_rec is None:
                    print(f"  [skip] Empty file: {result_file.name}")
                    continue

                model_name = first_rec.get("model_name", "UNKNOWN")
                prompt_style = first_rec.get("prompt_style", "UNKNOWN")

                if args.model_name and model_name != args.model_name:
                    continue
                if args.prompt_style and prompt_style != args.prompt_style:
                    continue

                print(f"\n  [{category}] {result_file.name}")
                print(f"    Model: {model_name} | Prompt: {prompt_style}")

                # Load gold data
                gold_by_id = load_translation_dataset(args.data_root, language, category)

                # Prepare data for XCOMET
                xcomet_data, valid_records = prepare_xcomet_data(
                    result_file, gold_by_id, args.max_examples
                )

                if not xcomet_data:
                    print(f"    [skip] No valid examples found")
                    continue

                # Run XCOMET evaluation
                try:
                    seg_scores, sys_score = run_xcomet_evaluation(
                        model, xcomet_data, batch_size=args.batch_size
                    )
                except Exception as e:
                    print(f"    [error] XCOMET evaluation failed: {e}")
                    continue

                # Attach scores to records
                scored_records = []
                for rec, seg_score in zip(valid_records, seg_scores):
                    scored_records.append({
                        **rec,
                        "xcomet_score": float(seg_score),
                    })

                # Save scored JSONL
                scored_file = result_file.with_name(result_file.stem + ".xcomet.jsonl")
                with scored_file.open("w", encoding="utf-8") as f:
                    for rec in scored_records:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"    → saved scored file: {scored_file}")

                # Compute aggregates
                stats = aggregate_statistics(seg_scores)
                stats["sys_score"] = float(sys_score) if sys_score is not None else None

                metrics_entry = {
                    "language": language,
                    "category": category,
                    "task": "translation",
                    "model_name": model_name,
                    "prompt_style": prompt_style,
                    "metric": "xcomet",
                    "model": args.xcomet_model,
                    "result_file": str(result_file),
                    **stats
                }
                all_metrics.append(metrics_entry)

                print(f"    avg_score={stats['avg_score']:.4f}")
                print(f"    sys_score={sys_score:.4f}" if sys_score is not None else "    sys_score=N/A")
                print(f"    coverage={stats['coverage']:.2%}")

    # Save summary JSON
    if all_metrics:
        summary_out = args.outputs_root / f"xcomet_eval_{args.language}_{args.model_name or 'all'}.json"            
        with summary_out.open("w", encoding="utf-8") as f:
            json.dump(all_metrics, f, ensure_ascii=False, indent=2)
        print(f"\n{'='*60}")
        print(f"Saved detailed metrics → {summary_out}")
        print(f"{'='*60}")

        # Create pivot table: model × category
        categories = sorted({m["category"] for m in all_metrics})
        models_prompts = sorted({(m["model_name"], m["prompt_style"]) for m in all_metrics})

        print(f"\n=== MODEL × CATEGORY TABLE (XCOMET) ===")
        print(f"Languages: {', '.join(languages)}")
        print(f"Metric: XCOMET (higher is better)")
        print(f"Model: {args.xcomet_model}\n")

        # Header
        header = ["model_name", "prompt_style"] + categories
        col_widths = [max(20, len(h)) for h in header]

        # Print header
        header_str = "  ".join(h.ljust(w) for h, w in zip(header, col_widths))
        print(header_str)
        print("-" * len(header_str))

        # Print rows
        for (mn, ps) in models_prompts:
            row_dict = {}
            for m in all_metrics:
                if (m["model_name"], m["prompt_style"]) == (mn, ps):
                    row_dict[m["category"]] = m["avg_score"]

            row = [mn[:18] + "..." if len(mn) > 20 else mn,
                   ps[:18] + "..." if len(ps) > 20 else ps]
            for cat in categories:
                score = row_dict.get(cat, None)
                if score is not None:
                    row.append(f"{score:.4f}")
                else:
                    row.append("N/A")

            row_str = "  ".join(cell.ljust(w) for cell, w in zip(row, col_widths))
            print(row_str)

        # Save CSV
        csv_out = args.outputs_root / f"xcomet_eval_{args.language}.csv"
        with csv_out.open("w", encoding="utf-8") as f:
            f.write(",".join(header) + "\n")
            for (mn, ps) in models_prompts:
                row = [mn, ps]
                for cat in categories:
                    score = next((m["avg_score"] for m in all_metrics
                                  if m["model_name"] == mn and m["prompt_style"] == ps and m["category"] == cat), None)
                    row.append(f"{score:.6f}" if score is not None else "")
                f.write(",".join(row) + "\n")
        print(f"\nSaved CSV → {csv_out}")
    else:
        print("\nNo metrics collected. Check that translation outputs exist.")


if __name__ == "__main__":
    main()
