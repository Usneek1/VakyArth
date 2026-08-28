import re

PREAMBLE_RE = re.compile(
    r"^(translation|answer|output|result|translated text)\s*:\s*",
    flags=re.IGNORECASE,
)


def build_prompt(item, language_module, category: str, prompt_style: str, script: str = "latin") -> str:
    source_text = item["source"]["scripts"][script]
    instruction, examples = language_module.translation_instruction(category=category, prompt_style=prompt_style, script=script)

    few_shot_text = ""
    for src, tgt in examples:
        few_shot_text += f"Source:\n{src}\n\nTranslation:\n{tgt}\n\n"

    prompt = (
        f"{instruction}\n\n"
        f"{few_shot_text}"
        f"Source:\n{source_text}\n\n"
        f"Translation:"
    )
    return prompt


def parse_output(item, raw_output: str, script: str = "latin") -> dict:
    reference = item.get("reference_translation", {}).get("text")

    if not raw_output or not raw_output.strip():
        return {"prediction": None, "reference": reference}

    lines = [PREAMBLE_RE.sub("", l).strip() for l in raw_output.strip().splitlines() if l.strip()]
    lines = [l for l in lines if l]

    if not lines:
        return {"prediction": None, "reference": reference}

    text = lines[0]
    words = text.split()
    if len(words) > 60:
        text = " ".join(words[:60])

    return {"prediction": text or None, "reference": reference}
