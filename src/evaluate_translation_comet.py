"""Translation evaluation using COMET (wmt22-comet-da).

Usage:
  python evaluate_translation_comet.py --language Punjabi
  python evaluate_translation_comet.py --language all
  python evaluate_translation_comet.py --language Hindi --model_name sarvam-105b
"""

import argparse
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from comet import download_model, load_from_checkpoint


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs_root", type=Path, default=Path("../outputs"))
    parser.add_argument("--data_root", type=Path, default=Path("../data"))
    parser.add_argument("--language", required=True, help="Language name or 'all'")
    parser.add_argument("--category", help="Optional: filter by category")
    parser.add_argument("--model_name", help="Optional: filter by model_name in JSONL")
    parser.add_argument("--prompt_style", help="Optional: filter by prompt_style in JSONL")
    parser.add_argument("--comet_model", default="Unbabel/wmt22-comet-da",
                        help="COMET model — default is wmt22-comet-da (~1.5GB, no gating)")
    #parser.add_argument("--comet_model", default="Unbabel/XCOMET-XL", help="COMET model — default is wmt22-comet-da (~1.5GB, no gating)")
    parser.add_argument("--max_examples", type=int)
    parser.add_argument("--batch_size", type=int, default=16)
    return parser.parse_args()


# ── Model loading ─────────────────────────────────────────────────────────────

def load_comet_model(model_id: str):
    print(f"[comet] Downloading/loading: {model_id}")
    path = download_model(model_id)
    model = load_from_checkpoint(path)
    model.eval()
    print(f"[comet] Model ready")
    return model


# ── Gold data ─────────────────────────────────────────────────────────────────

def load_gold(data_root: Path, language: str, category: str) -> Dict[str, dict]:
    path = data_root / language / category / "translation.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    return {item["id"]: item for item in items if "id" in item}


def get_reference(gold_item: dict) -> str:
    return gold_item.get("reference_translation", {}).get("text", "")


def get_source(gold_item: dict) -> str:
    """Pull source text — handles both flat string and nested scripts dict."""
    src = gold_item.get("source", "")
    if isinstance(src, str):
        return src
    if isinstance(src, dict):
        scripts = src.get("scripts", {})
        if isinstance(scripts, dict):
            latin = scripts.get("latin", {})
            if isinstance(latin, dict):
                return latin.get("source", "")
    return ""


# ── Data preparation ──────────────────────────────────────────────────────────

def prepare_comet_data(result_file, gold_by_id, max_examples):
    records = []
    with result_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if max_examples:
        records = records[:max_examples]

    comet_inputs = []
    valid_records = []

    for rec in records:
        ex_id = rec.get("id", "")
        
        # Handle both formats: prediction as string or as dict with "text" key
        pred = rec.get("prediction", {})
        if isinstance(pred, dict):
            hypothesis = (pred.get("prediction") or pred.get("text") or "").strip()
        else:
            hypothesis = str(pred).strip() if pred else ""

        gold_item = gold_by_id.get(ex_id, {})
        reference = get_reference(gold_item)
        source = get_source(gold_item)

        if not hypothesis:
            print(f"  [skip] empty hypothesis: {ex_id}")
            continue
        if not reference:
            print(f"  [skip] no reference: {ex_id}")
            continue

        comet_inputs.append({"src": source, "mt": hypothesis, "ref": reference})
        valid_records.append(rec)

    return comet_inputs, valid_records


# ── Evaluation ────────────────────────────────────────────────────────────────

def run_comet(model, comet_inputs: List[dict], batch_size: int) -> Tuple[List[float], float]:
    import torch
    gpus = 1 if torch.cuda.is_available() else 0
    output = model.predict(comet_inputs, batch_size=batch_size, gpus=gpus)
    return output.scores, output.system_score


def aggregate(scores: List[float]) -> dict:
    arr = np.array(scores)
    return {
        "num_scored": len(arr),
        "avg_score": float(np.mean(arr)),
        "median_score": float(np.median(arr)),
        "std_score": float(np.std(arr)),
        "min_score": float(np.min(arr)),
        "max_score": float(np.max(arr)),
        "q25_score": float(np.percentile(arr, 25)),
        "q75_score": float(np.percentile(arr, 75)),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    languages = (
        [d.name for d in args.outputs_root.iterdir() if d.is_dir()]
        if args.language.lower() == "all"
        else [args.language]
    )

    model = load_comet_model(args.comet_model)
    all_metrics = []

    for language in languages:
        lang_dir = args.outputs_root / language
        if not lang_dir.exists():
            continue

        print(f"\n{'='*60}\nLanguage: {language}\n{'='*60}")

        for cat_dir in sorted(lang_dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            category = cat_dir.name
            if args.category and category != args.category:
                continue

            task_dir = cat_dir / "translation"
            if not task_dir.exists():
                continue

            gold_by_id = load_gold(args.data_root, language, category)

            for result_file in sorted(task_dir.glob("*.jsonl")):
                # skip files we already scored
                if ".comet." in result_file.name:
                    continue

                # peek at first record for metadata
                try:
                    with result_file.open("r", encoding="utf-8") as f:
                        first = json.loads(next(l for l in f if l.strip()))
                except StopIteration:
                    continue

                model_name = first.get("model_name", "UNKNOWN")
                prompt_style = first.get("prompt_style", "UNKNOWN")

                if args.model_name and model_name != args.model_name:
                    continue
                if args.prompt_style and prompt_style != args.prompt_style:
                    continue

                print(f"\n  [{category}] {result_file.name}")

                comet_inputs, valid_records = prepare_comet_data(
                    result_file, gold_by_id, args.max_examples
                )

                if not comet_inputs:
                    print("  [skip] no valid examples")
                    continue

                seg_scores, sys_score = run_comet(model, comet_inputs, args.batch_size)

                # ── Save judged file (one entry per line with score attached) ──
                judged_file = result_file.with_name(
                    result_file.stem + ".comet.jsonl"
                )
                with judged_file.open("w", encoding="utf-8") as f:
                    for rec, score, inp in zip(valid_records, seg_scores, comet_inputs):
                        judged_rec = {
                            **rec,
                            "comet_score": round(float(score), 6),
                            "comet_src": inp["src"],
                            "comet_ref": inp["ref"],
                            "comet_hyp": inp["mt"],
                        }
                        f.write(json.dumps(judged_rec, ensure_ascii=False) + "\n")
                print(f"  → judged file: {judged_file.name}")

                # ── Aggregate stats ───────────────────────────────────────────
                stats = aggregate(seg_scores)
                print(f"  avg={stats['avg_score']:.4f}  "
                      f"sys={sys_score:.4f}  "
                      f"n={stats['num_scored']}")

                all_metrics.append({
                    "language": language,
                    "category": category,
                    "task": "translation",
                    "model_name": model_name,
                    "prompt_style": prompt_style,
                    "comet_model": args.comet_model,
                    "sys_score": float(sys_score),
                    "result_file": str(result_file),
                    **stats,
                })

    if not all_metrics:
        print("\nNo results found.")
        return

    # ── Summary JSON ──────────────────────────────────────────────────────────
    suffix = args.language
    summary_out = args.outputs_root / f"comet_eval_{suffix}.json"
    with summary_out.open("w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    print(f"\nSaved summary → {summary_out}")

    # ── Pivot table ───────────────────────────────────────────────────────────
    categories = sorted({m["category"] for m in all_metrics})
    model_prompts = sorted({(m["model_name"], m["prompt_style"]) for m in all_metrics})

    header = ["model_name", "prompt_style"] + categories
    col_w = [max(20, len(h)) for h in header]

    print(f"\n=== COMET ({args.comet_model}) ===")
    print("  ".join(h.ljust(w) for h, w in zip(header, col_w)))
    print("-" * (sum(col_w) + 2 * len(col_w)))

    for (mn, ps) in model_prompts:
        scores = {
            m["category"]: m["avg_score"]
            for m in all_metrics
            if m["model_name"] == mn and m["prompt_style"] == ps
        }
        row = [mn[:19] if len(mn) > 20 else mn, ps]
        row += [f"{scores[c]:.4f}" if c in scores else "N/A" for c in categories]
        print("  ".join(str(v).ljust(w) for v, w in zip(row, col_w)))

    # ── CSV ───────────────────────────────────────────────────────────────────
    csv_out = args.outputs_root / f"comet_eval_{suffix}.csv"
    with csv_out.open("w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        for (mn, ps) in model_prompts:
            scores = {
                m["category"]: m["avg_score"]
                for m in all_metrics
                if m["model_name"] == mn and m["prompt_style"] == ps
            }
            row = [mn, ps] + [f"{scores[c]:.6f}" if c in scores else "" for c in categories]
            f.write(",".join(row) + "\n")
    print(f"Saved CSV → {csv_out}")


if __name__ == "__main__":
    main()