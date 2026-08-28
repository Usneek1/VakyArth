"""Main script for running the VakyArth pragmatics benchmark evaluation.

Orchestrates model inference across languages, categories (phenomena), and
task types (mcqs / nli / translation), and writes raw model outputs as JSONL
under `output_root/<Language>/<Category>/<Task>/`.

Usage:
    python main.py --language Hindi --category implicature --task mcqs \
        --model_name Qwen/Qwen2.5-7B-Instruct

    python main.py --model_name sarvamai/sarvam-105b   # all languages/categories/tasks
"""
import argparse
import json
import time
from pathlib import Path

from model import HFModelRunner
from sarvam import SarvamRunner
from cohere_runner import CohereRunner
from tasks import mcq as mcq_task
from tasks import nli as nli_task
from tasks import translation as translation_task
from languages import punjabi, hindi, tamil, malayalam

LANG_MODULE_MAP = {
    "Punjabi": punjabi,
    "Hindi": hindi,
    "Tamil": tamil,
    "Malayalam": malayalam,
}

TASK_MODULE_MAP = {
    "mcqs": mcq_task,
    "nli": nli_task,
    "translation": translation_task,
}

# Native script used by each language, selected via --script native
LANG_SCRIPT_MAP = {
    "Hindi": "devanagari",
    "Tamil": "tamil",
    "Punjabi": "gurmukhi",
    "Malayalam": "malayalam",
}

# Only API runners need rate-limit sleep
API_SLEEP_SECONDS = 2


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", help="Punjabi / Hindi / Tamil / Malayalam. Default: all.")
    parser.add_argument("--category", nargs="+", help="One or more categories, e.g. implicature deixis. Default: all.")
    parser.add_argument("--task", choices=["mcqs", "nli", "translation"], help="Default: all tasks in each category.")
    parser.add_argument("--model_name", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--prompt_style", default="direct", choices=["direct", "fewshot"])
    parser.add_argument("--script", default="latin", choices=["latin", "native"],
                        help="Which script to present source text in. Default: latin.")
    parser.add_argument("--data_root", type=Path, default=Path("../data"))
    parser.add_argument("--output_root", type=Path, default=Path("../outputs"))
    parser.add_argument("--max_examples", type=int)
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.2)
    return parser.parse_args()


def slugify_model_name(model_name: str) -> str:
    return model_name.replace("/", "_").replace(":", "_")


def load_dataset(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Invalid dataset structure in {path}")


def get_all_languages(data_root: Path):
    return [d.name for d in sorted(data_root.iterdir()) if d.is_dir() and d.name in LANG_MODULE_MAP]


def get_categories(lang_dir: Path):
    return [d.name for d in sorted(lang_dir.iterdir()) if d.is_dir()]


def get_runner(model_name: str):
    if model_name.lower().startswith("sarvamai/"):
        return SarvamRunner(model_name=model_name), True   # (runner, is_api)
    if model_name.lower().startswith("cohere/"):
        return CohereRunner(model_name=model_name), True   # (runner, is_api)
    return HFModelRunner(model_name=model_name), False


def main():
    args = parse_args()
    model_slug = slugify_model_name(args.model_name)
    model, is_api = get_runner(args.model_name)

    languages = [args.language] if args.language else get_all_languages(args.data_root)

    for lang in languages:
        lang_dir = args.data_root / lang
        if not lang_dir.exists():
            print(f"[SKIP] Language directory not found: {lang_dir}")
            continue

        # Resolve script key for this language (e.g. --script native -> "devanagari" for Hindi)
        script = LANG_SCRIPT_MAP.get(lang, "latin") if args.script == "native" else "latin"

        lang_module = LANG_MODULE_MAP[lang]
        categories = args.category if args.category else get_categories(lang_dir)

        for category in categories:
            category_dir = lang_dir / category
            if not category_dir.exists():
                continue

            tasks = [args.task] if args.task else list(TASK_MODULE_MAP.keys())

            for task in tasks:
                task_file = category_dir / f"{task}.json"
                if not task_file.exists():
                    continue

                task_module = TASK_MODULE_MAP[task]
                items = load_dataset(task_file)
                if args.max_examples:
                    items = items[:args.max_examples]

                out_dir = args.output_root / lang / category / task
                out_dir.mkdir(parents=True, exist_ok=True)
                # Include script in filename so latin and native results don't overwrite each other
                out_file = out_dir / f"results__{model_slug}__{args.prompt_style}__{args.script}.jsonl"

                with out_file.open("w", encoding="utf-8") as fout:
                    for item in items:
                        try:
                            prompt = task_module.build_prompt(
                                item=item,
                                language_module=lang_module,
                                category=category,
                                prompt_style=args.prompt_style,
                                script=script,
                            )
                        except KeyError:
                            print(f"[SKIP] Missing script '{script}' for item {item.get('id')}")
                            continue

                        completion = model.generate(
                            prompt,
                            max_new_tokens=args.max_new_tokens,
                            temperature=args.temperature,
                        )

                        prediction = task_module.parse_output(item, completion, script=script)

                        record = {
                            "id": item["id"],
                            "language": lang,
                            "category": category,
                            "task": task,
                            "model_name": args.model_name,
                            "prompt_style": args.prompt_style,
                            "script": args.script,
                            "prompt": prompt,
                            "raw_output": completion,
                            "prediction": prediction,
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")

                        if is_api:
                            time.sleep(API_SLEEP_SECONDS)

                print(f"[DONE] {lang}/{category}/{task} -> {out_file}")


if __name__ == "__main__":
    main()
