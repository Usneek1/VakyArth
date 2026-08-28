import re


def _extract_context(s: dict) -> str:
    if "context" in s:
        return s["context"]
    turns = [f'{t["speaker"]}: {t["utterance"]}' for t in s.get("dialogue", [])]
    return "\n".join(turns)


def build_prompt(item, language_module, category: str, prompt_style: str, script: str = "latin") -> str:
    s = item["scripts"][script]
    context_str = _extract_context(s)
    options = s["options"]
    opt_lines = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])

    instruction, examples = language_module.mcq_instruction(category=category, prompt_style=prompt_style, script=script)

    few_shot_text = ""
    for ctx, opts, answer in examples:
        few_shot_text += (
            f"Context:\n{ctx}\n\n"
            f"Options:\n{opts}\n\n"
            f"Answer:\n{answer}\n\n"
        )

    prompt = (
        f"{instruction}\n\n"
        f"{few_shot_text}"
        f"Context:\n{context_str}\n\n"
        f"Question:\n{s['question']}\n\n"
        f"Options:\n{opt_lines}\n\n"
        f"Answer:"
    )
    return prompt


def parse_output(item, raw_output: str, script: str = "latin") -> dict:
    s = item["scripts"][script]
    options = s["options"]
    reference = s["answer"]

    text = raw_output.strip().upper()

    match = re.search(r'\b([A-E])[.):\s]', text)
    if not match and text and text[0] in "ABCDE":
        match_letter = text[0]
    else:
        match_letter = match.group(1) if match else None

    if match_letter:
        index = ord(match_letter) - ord("A")
        if 0 <= index < len(options):
            return {
                "prediction": {"label": match_letter, "index": index, "text": options[index]},
                "reference": reference,
            }

    return {"prediction": {"label": None, "index": None, "text": None}, "reference": reference}
