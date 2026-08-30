"""Evaluation module for pragmatics benchmark outputs.

This module evaluates model predictions against for MCQ and NLI tasks. It generates detailed JSON reports
and CSV pivot tables for analysis.
"""
import argparse
import json
from pathlib import Path
from typing import Dict, Tuple, Any, List


DATA_TASKS = {"mcqs", "nli"}


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate pragmatics benchmark outputs")

    parser.add_argument(
        "--data_root",
        type=Path,
        default=Path("../data"),
        help="Root of gold datasets: data/<Language>/<Category>/<task>.json",
    )

    parser.add_argument(
        "--outputs_root",
        type=Path,
        default=Path("../outputs"),
        help="Root of model outputs: outputs/<Language>/<Category>/<task>/*.jsonl",
    )

    parser.add_argument(
        "--language",
        required=True,
        help="Language folder name (e.g. Punjabi, Hindi).",
    )

    parser.add_argument(
        "--category",
        help="Optional filter: Category folder name (e.g. Deixis, Implicature). Default: all.",
    )

    parser.add_argument(
        "--task",
        choices=["mcqs", "nli"],
        help="Optional filter: Task type. Default: all.",
    )

    parser.add_argument(
        "--model_name",
        help="Optional filter: only evaluate outputs from this model_name (matching field in JSONL).",
    )

    parser.add_argument(
        "--prompt_style",
        help="Optional filter: only evaluate this prompt_style (matching field in JSONL).",
    )

    return parser.parse_args()


# ---------- GOLD INDEXING ----------

def load_dataset(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported dataset structure in {path}")


def build_gold_index(
    data_root: Path,
) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    """
    Build a mapping:
      (language, category, task) -> { id -> gold_item }
    where language/category/task are the folder/task names used in data/.
    """
    gold_index: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    for lang_dir in data_root.iterdir():
        if not lang_dir.is_dir():
            continue
        language = lang_dir.name

        for cat_dir in lang_dir.iterdir():
            if not cat_dir.is_dir():
                continue
            category = cat_dir.name

            for json_file in cat_dir.glob("*.json"):
                task = json_file.stem  # mcq / nli / generation
                if task not in DATA_TASKS:
                    continue

                items = load_dataset(json_file)
                key = (language, category, task)
                id_map = {}
                for item in items:
                    item_id = item.get("id")
                    if item_id is None:
                        continue
                    id_map[item_id] = item
                gold_index[key] = id_map

    return gold_index


# ---------- METRIC COMPUTATION HELPERS ----------

def get_mcq_gold_label(item: dict) -> str:
    # The answer letter (A/B/C/D) is the same across script variants of an
    # item, so prefer latin but fall back to any other available script --
    # a handful of items (e.g. ma_imp_mcq_009) have no latin block at all,
    # which only matters when scoring a --script native run.
    scripts = item.get("scripts", {})
    for key in ("latin", *scripts.keys()):
        if key in scripts and "answer" in scripts[key]:
            return scripts[key]["answer"]["label"].upper()
    raise KeyError(f"No script with an answer found for item {item.get('id')}")


def get_nli_gold_label(item: dict) -> str:
    # label is top-level on every NLI item (see data/README.md schema)
    label = item.get("label")
    if label is None:
        print(f"[WARN] Missing 'label' for id={item.get('id')}")
        return None
    return label.lower()

def evaluate_mcq(records, gold_by_id):
    total = 0
    covered = 0
    correct = 0

    for rec in records:
        ex_id = rec["id"]
        gold_item = gold_by_id.get(ex_id)
        if gold_item is None:
            continue

        total += 1

        gold_label = get_mcq_gold_label(gold_item)
        pred = rec.get("prediction", {}).get("prediction", {})          # fixed
        pred_label = pred.get("label") if isinstance(pred, dict) else None  # fixed

        if pred_label is None:
            continue

        covered += 1
        if pred_label.upper() == gold_label:
            correct += 1

    acc = correct / total if total > 0 else 0.0
    coverage = covered / total if total > 0 else 0.0
    acc_cov = correct / covered if covered > 0 else 0.0

    return {
        "task": "mcqs",
        "num_examples": total,
        "num_covered": covered,
        "num_correct": correct,
        "accuracy": acc,
        "coverage": coverage,
        "accuracy_on_covered": acc_cov,
    }


def evaluate_nli(records, gold_by_id):
    labels = ["entailment", "contradiction", "neutral"]
    label_to_idx = {l: i for i, l in enumerate(labels)}
    confusion = [[0 for _ in labels] for _ in labels]

    total = 0
    correct = 0

    for rec in records:
        ex_id = rec["id"]
        gold_item = gold_by_id.get(ex_id)
        if gold_item is None:
            continue

        gold_label = get_nli_gold_label(gold_item)
        if gold_label not in label_to_idx:
            continue

        pred = rec.get("prediction", {}).get("prediction")              # fixed
        pred_label = pred.lower() if isinstance(pred, str) else ""      # fixed

        if pred_label not in label_to_idx:
            total += 1
            continue

        total += 1
        if pred_label == gold_label:
            correct += 1

        gi = label_to_idx[gold_label]
        pi = label_to_idx[pred_label]
        confusion[gi][pi] += 1

    acc = correct / total if total > 0 else 0.0

    f1_per_label = {}
    for i, lbl in enumerate(labels):
        tp = confusion[i][i]
        fp = sum(confusion[r][i] for r in range(len(labels)) if r != i)
        fn = sum(confusion[i][c] for c in range(len(labels)) if c != i)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec_score = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec_score / (prec + rec_score) if (prec + rec_score) > 0 else 0.0
        f1_per_label[lbl] = f1

    macro_f1 = sum(f1_per_label.values()) / len(labels)

    return {
        "task": "nli",
        "num_examples": total,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "f1_per_label": f1_per_label,
        "confusion_matrix": {
            "labels": labels,
            "matrix": confusion,
        },
    }


# ---------- MAIN EVAL LOOP + PIVOT ----------

def main():
    args = parse_args()
    language = args.language

    # 1) Build gold index once
    gold_index = build_gold_index(args.data_root)

    # 2) Scan outputs tree for the given language only
    metrics_by_group = []

    lang_dir = args.outputs_root / language
    if not lang_dir.exists():
        print(f"No outputs found for language: {language}")
        return

    for cat_dir in lang_dir.iterdir():
        if not cat_dir.is_dir():
            continue
        category = cat_dir.name
        if args.category and category != args.category:
            continue

        for task_dir in cat_dir.iterdir():
            if not task_dir.is_dir():
                continue
            task = task_dir.name
            if args.task and task != args.task:
                continue

            # we only automatically evaluate mcq + nli
            if task not in {"mcqs", "nli"}:
                continue

            for result_file in task_dir.glob("*.jsonl"):
                # load all records
                records = []
                with result_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        rec = json.loads(line)
                        records.append(rec)

                if not records:
                    continue

                # read model_name / prompt_style from first record
                model_name = records[0].get("model_name", "UNKNOWN")
                prompt_style = records[0].get("prompt_style", "UNKNOWN")

                if args.model_name and model_name != args.model_name:
                    continue
                if args.prompt_style and prompt_style != args.prompt_style:
                    continue

                gold_by_id = gold_index.get((language, category, task))
                if gold_by_id is None:
                    print(f"[WARN] No gold dataset for {language}/{category}/{task}, skipping {result_file}")
                    continue

                if task == "mcqs":
                    m = evaluate_mcq(records, gold_by_id)
                    score = m["accuracy"]  # choose accuracy as main scalar
                elif task == "nli":
                    m = evaluate_nli(records, gold_by_id)
                    score = m["accuracy"]
                else:
                    continue

                group_info = {
                    "language": language,
                    "category": category,
                    "task": task,
                    "model_name": model_name,
                    "prompt_style": prompt_style,
                    "result_file": str(result_file),
                    "score": score,
                }
                group_info.update(m)
                metrics_by_group.append(group_info)

    if not metrics_by_group:
        print("No matching evaluation results found for this language/filters.")
        return

    # Save detailed JSON as before
    summary_out = args.outputs_root / f"evaluation_summary_{language}.json"
    with summary_out.open("w", encoding="utf-8") as f:
        json.dump(metrics_by_group, f, ensure_ascii=False, indent=2)
    print(f"Saved detailed metrics to {summary_out}")

    # 3) Pivot into model x (category,task) table
    # Determine all categories/tasks present
    categories = sorted({m["category"] for m in metrics_by_group})
    tasks = sorted({m["task"] for m in metrics_by_group})  # should be ['mcq','nli'] ideally

    col_keys = []
    for cat in categories:
        for t in tasks:
            col_keys.append((cat, t))

    # Group metrics by model_name (and prompt_style if you want separate rows per style)
    # Here we treat each (model_name, prompt_style) as one row; you can drop prompt_style if needed.
    rows = {}
    for m in metrics_by_group:
        key = (m["model_name"], m["prompt_style"])
        if key not in rows:
            rows[key] = {}
        rows[key][(m["category"], m["task"])] = m["score"]

    # 4) Print a nice table: rows = models, columns = category_task
    print("\n=== MODEL × CATEGORY/TASK TABLE ===")
    print(f"Language: {language}")
    if args.prompt_style:
        print(f"Prompt style: {args.prompt_style}")
    print()

    # Build header
    header_cells = ["model_name", "prompt_style"]
    for cat, t in col_keys:
        header_cells.append(f"{cat}_{t}")
    col_widths = [max(len(h), 12) for h in header_cells]

    def fmt_row(vals):
        return "  ".join(str(v).ljust(w) for v, w in zip(vals, col_widths))

    print(fmt_row(header_cells))
    print("-" * sum(col_widths) + "-" * (2 * len(col_widths)))

    # Print one row per (model_name, prompt_style)
    for (model_name, prompt_style), cell_scores in sorted(rows.items(), key=lambda x: x[0][0]):
        row_vals = [model_name, prompt_style]
        for cat, t in col_keys:
            v = cell_scores.get((cat, t))
            if v is None:
                row_vals.append("NA")
            else:
                row_vals.append(f"{v:.3f}")
        print(fmt_row(row_vals))

    # 5) Also dump as CSV for easy plotting
    csv_out = args.outputs_root / f"evaluation_table_{language}.csv"
    with csv_out.open("w", encoding="utf-8") as f:
        f.write(",".join(header_cells) + "\n")
        for (model_name, prompt_style), cell_scores in sorted(rows.items(), key=lambda x: x[0][0]):
            row_vals = [model_name, prompt_style]
            for cat, t in col_keys:
                v = cell_scores.get((cat, t))
                if v is None:
                    row_vals.append("")
                else:
                    row_vals.append(f"{v:.4f}")
            f.write(",".join(row_vals) + "\n")

    print(f"\nSaved pivot table CSV to {csv_out}")


if __name__ == "__main__":
    main()
