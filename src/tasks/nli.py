def _extract_premise(s: dict) -> str:
    if isinstance(s.get("premise"), list):
        return "\n".join([f'{t["speaker"]}: {t["utterance"]}' for t in s["premise"]])
    return s.get("premise", "")


def build_prompt(item, language_module, category: str, prompt_style: str, script: str = "latin") -> str:
    s = item["scripts"][script]
    premise_str = _extract_premise(s)
    hypothesis = s["hypothesis"]

    instruction, examples = language_module.nli_instruction(category=category, prompt_style=prompt_style, script=script)

    few_shot_text = ""
    for premise, hyp, label in examples:
        few_shot_text += (
            f"Premise:\n{premise}\n\n"
            f"Hypothesis:\n{hyp}\n\n"
            f"Label:\n{label}\n\n"
        )

    prompt = (
        f"{instruction}\n\n"
        f"{few_shot_text}"
        f"Premise:\n{premise_str}\n\n"
        f"Hypothesis:\n{hypothesis}\n\n"
        f"Label:"
    )
    return prompt


def parse_output(item, raw_output: str, script: str = "latin") -> dict:
    reference = item.get("label")  # top-level label field

    text = raw_output.strip().lower()
    prediction = None
    for candidate in ["entailment", "contradiction", "neutral"]:
        if candidate in text:
            prediction = candidate
            break

    return {"prediction": prediction, "reference": reference}
