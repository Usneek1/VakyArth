"""
Hindi Language Prompt Instruction
"""
def mcq_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    instruction = (
        "Is prashan ka sahi uttar kya hai?\n"
        "Jabab mein sirf option ka akshar (A/B/C...) aur us option ka text likho."
    )
    if prompt_style == "fewshot":
        examples = [
            (
                'Priya ne kaha, "Aaj khana bahut achha bana hai."',
                "A. Priya ko khana pasand aaya\nB. Priya ne khana nahi khaya\nC. Priya ne khana banaya\nD. Priya ko bhook nahi thi",
                "A. Priya ko khana pasand aaya",
            ),
            (
                'Ramesh ne kaha, "Bahar bahut thand hai." Lekin use bahar jaana tha.',
                "A. Ramesh bahar nahi jayega\nB. Ramesh bahar jayega\nC. Ramesh ko thand nahi lagti\nD. Ramesh ghar mein rehna chahta hai",
                "B. Ramesh bahar jayega",
            ),
            (
                'Maa ne kaha, "Koi baat nahi, agli baar dhyan rakhna."',
                "A. Maa gusse mein hai\nB. Maa ne maafi maangi\nC. Maa ne tasalli di\nD. Maa ne saza di",
                "C. Maa ne tasalli di",
            ),
        ]
    else:
        examples = []
    return instruction, examples


def nli_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    # Native-script (devanagari) instructions not yet authored; falls back to latin for all scripts.
    instruction = (
        "Neeche diye gaye do vaakyon ke beech sambandh batao.\n"
        "Jabab mein sirf 'Entailment', 'Contradiction', ya 'Neutral' likho."
    )
    if prompt_style == "fewshot":
        examples = [
            (
                "A: Khana taiyaar hai?\nB: Main abhi bazaar gaya tha.",
                "Khana taiyaar hai.",
                "Contradiction",
            ),
            (
                "A: Kya tujhe pata hai kal chutti hai?\nB: Haan, main subah se plan kar raha hoon.",
                "B kal kuch karna chahta hai.",
                "Entailment",
            ),
            (
                "A: Bahar baarish ho rahi hai.\nB: Theek hai.",
                "B bahar jayega.",
                "Neutral",
            ),
        ]
    else:
        examples = []
    return instruction, examples


def translation_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    # Native-script (devanagari) instructions not yet authored; falls back to latin for all scripts.
    instruction = (
        "Neeche diye gaye Hindi text ko English mein anuvad karo.\n"
        "Sirf translated text hi output mein dikhayein."
    )
    if prompt_style == "fewshot":
        examples = [
            ("Unhone milkar kaam kiya.", "They worked together."),
            ("Bazaar mein bahut saamaan milta hai.", "A wide variety of goods is available in the market."),
            ("Usne apna vaada nibhaya aur samay par pahunch gaya.", "He kept his promise and arrived on time."),
        ]
    else:
        examples = []
    return instruction, examples
