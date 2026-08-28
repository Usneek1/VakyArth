def mcq_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    if script == "gurmukhi":
        instruction = (
            "ਇਸ ਪ੍ਰਸ਼ਨ ਦਾ ਕੀ ਸਹੀ ਉੱਤਰ ਹੈ?\n"
            "ਜਵਾਬ ਵਿੱਚ ਸਿਰਫ਼ ਆਪਸ਼ਨ ਲੈਟਰ (A/B/C...) ਤੇ ਉਸਦੀ ਆਪਸ਼ਨ ਟੈਕਸਟ ਲਿਖੋ।"
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    'ਸੀਮਾ ਨੇ ਕਿਹਾ, "ਬਹੁਤ ਵਧੀਆ ਖਾਣਾ ਬਣਾਇਆ ਤੁਸੀਂ।"',
                    "A. ਸੀਮਾ ਨੂੰ ਖਾਣਾ ਪਸੰਦ ਆਇਆ\nB. ਸੀਮਾ ਨੂੰ ਖਾਣਾ ਪਸੰਦ ਨਹੀਂ ਆਇਆ\nC. ਸੀਮਾ ਨੇ ਖਾਣਾ ਨਹੀਂ ਖਾਧਾ\nD. ਸੀਮਾ ਨੇ ਖਾਣਾ ਬਣਾਇਆ",
                    "A. ਸੀਮਾ ਨੂੰ ਖਾਣਾ ਪਸੰਦ ਆਇਆ",
                ),
                (
                    'ਰਵੀ ਨੇ ਕਿਹਾ, "ਅੱਜ ਬਹੁਤ ਠੰਡ ਆ।" ਲੇਕਿਨ ਉਸਨੇ ਬਾਹਰ ਜਾਣਾ ਸੀ।',
                    "A. ਰਵੀ ਬਾਹਰ ਨਹੀਂ ਜਾਵੇਗਾ\nB. ਰਵੀ ਬਾਹਰ ਜਾਵੇਗਾ\nC. ਰਵੀ ਨੂੰ ਠੰਡ ਨਹੀਂ ਲੱਗਦੀ\nD. ਰਵੀ ਘਰ ਵਿੱਚ ਰਹਿਣਾ ਚਾਹੁੰਦਾ ਹੈ",
                    "B. ਰਵੀ ਬਾਹਰ ਜਾਵੇਗਾ",
                ),
                (
                    'ਮਾਂ ਨੇ ਕਿਹਾ, "ਕੋਈ ਗੱਲ ਨਹੀਂ, ਅਗਲੀ ਵਾਰ ਸਹੀ ਕਰ ਲੈਣਾ।"',
                    "A. ਮਾਂ ਗੁੱਸੇ ਵਿੱਚ ਹੈ\nB. ਮਾਂ ਨੇ ਮਾਫ਼ੀ ਮੰਗੀ\nC. ਮਾਂ ਨੇ ਤਸੱਲੀ ਦਿੱਤੀ\nD. ਮਾਂ ਨੇ ਸਜ਼ਾ ਦਿੱਤੀ",
                    "C. ਮਾਂ ਨੇ ਤਸੱਲੀ ਦਿੱਤੀ",
                ),
            ]
        else:
            examples = []
    else:  # latin
        instruction = (
            "Iss prashan da ki sahi uttar hai?\n"
            "Jawab vich sirf option letter (A/B/C...) te usdi option text likho."
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    'Seema ne keha, "Bahut vadiya khaana banaaya tusi."',
                    "A. Seema nu khaana pasand aaya\nB. Seema nu khaana pasand nahi aaya\nC. Seema ne khaana nahi khaadha\nD. Seema ne khaana banaaya",
                    "A. Seema nu khaana pasand aaya",
                ),
                (
                    'Ravi ne keha, "Aj bahut thand aa." Lekin usne bahar jaana si.',
                    "A. Ravi bahar nahi jaayega\nB. Ravi bahar jaayega\nC. Ravi nu thand nahi lagdi\nD. Ravi ghar vich rehna chahunda hai",
                    "B. Ravi bahar jaayega",
                ),
                (
                    'Mama ne keha, "Koi gal nahi, agli baar sahi kar lena."',
                    "A. Mama gusse vich hai\nB. Mama ne maafi mangi\nC. Mama ne tasalli ditti\nD. Mama ne sazaa ditti",
                    "C. Mama ne tasalli ditti",
                ),
            ]
        else:
            examples = []

    return instruction, examples


def nli_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    if script == "gurmukhi":
        instruction = (
            "ਹੇਠ ਲਿਖੇ ਗਏ ਦੋ ਵਾਕਿਆਂ ਦੇ ਵਿਚਕਾਰ ਸੰਬੰਧ ਦੱਸੋ।\n"
            "ਜਵਾਬ ਵਿੱਚ ਸਿਰਫ਼ 'Entailment', 'Contradiction', ਜਾਂ 'Neutral' ਲਿਖੋ।"
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    "A: ਖਾਣਾ ਤਿਆਰ ਹੈ?\nB: ਮੈਂ ਹੁਣੇ ਬਾਜ਼ਾਰ ਗਿਆ ਸੀ।",
                    "ਖਾਣਾ ਤਿਆਰ ਹੈ।",
                    "Contradiction",
                ),
                (
                    "A: ਤੈਨੂੰ ਪਤਾ ਹੈ ਕੱਲ੍ਹ ਛੁੱਟੀ ਹੈ?\nB: ਹਾਂ, ਮੈਂ ਸਵੇਰ ਤੋਂ ਪਲੈਨ ਕਰ ਰਿਹਾ ਹਾਂ।",
                    "B ਕੱਲ੍ਹ ਕੁਝ ਕਰਨਾ ਚਾਹੁੰਦਾ ਹੈ।",
                    "Entailment",
                ),
                (
                    "A: ਬਾਹਰ ਮੀਂਹ ਪੈ ਰਿਹਾ ਹੈ।\nB: ਠੀਕ ਆ।",
                    "B ਬਾਹਰ ਜਾਵੇਗਾ।",
                    "Neutral",
                ),
            ]
        else:
            examples = []
    else:  # latin
        instruction = (
            "Heth likhe gaye do vaakyan de vichkaar sambandh daso.\n"
            "Jawab vich sirf 'Entailment', 'Contradiction', ja 'Neutral' likho."
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    "A: Khaana taiyaar hai?\nB: Main abhi baazaar gaya si.",
                    "Khaana taiyaar hai.",
                    "Contradiction",
                ),
                (
                    "A: Tenu pata hai kal chutti hai?\nB: Haan, main subah ton plan kar raha haan.",
                    "B kal kuch karna chahunda hai.",
                    "Entailment",
                ),
                (
                    "A: Bahar meenh pad raha hai.\nB: Theek aa.",
                    "B bahar jaayega.",
                    "Neutral",
                ),
            ]
        else:
            examples = []

    return instruction, examples


def translation_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    instruction = (
        "Translate the following Punjabi text into natural, idiomatic English.\n"
        "Output only the translated text."
    )
    if prompt_style == "fewshot":
        examples = [
            ("Unhan ne ral ke kaam kita.", "They worked together."),
            ("Bazaar vich bahut saara samaan milda hai.", "A wide variety of goods is available in the market."),
            ("Usne apna vaada nibhaya ate samay sir pahunch gaya.", "He kept his promise and arrived on time."),
        ]
    else:
        examples = []
    return instruction, examples
