def mcq_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    if script == "tamil":
        instruction = (
            "இந்தக் கேள்விக்கு பதில் என்ன?\n"
            "சரியான option letter (A/B/C/D) உம் சரியான option-இல் உள்ள பதில் மட்டும் கொடுக்க வேண்டும்."
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    'பிரியா சொன்னாள், "இன்னிக்கு சாப்பாடு ரொம்ப நல்லா இருக்கு."',
                    "A. பிரியாவுக்கு சாப்பாடு பிடிச்சிருக்கு\nB. பிரியா சாப்பிடல\nC. பிரியா சாப்பாடு செஞ்சாள்\nD. பிரியாவுக்கு பசி இல்லை",
                    "A. பிரியாவுக்கு சாப்பாடு பிடிச்சிருக்கு",
                ),
                (
                    'ராஜன் சொன்னான், "வெளியில் ரொம்ப குளிர் இருக்கு." ஆனா அவன் வெளியில் போகணும்.',
                    "A. ராஜன் வெளியில் போகமாட்டான்\nB. ராஜன் வெளியில் போவான்\nC. ராஜனுக்கு குளிர் தெரியாது\nD. ராஜன் வீட்டிலயே இருப்பான்",
                    "B. ராஜன் வெளியில் போவான்",
                ),
                (
                    'அம்மா சொன்னாள், "பரவாலா, next time கவனம் ஆ இரு."',
                    "A. அம்மா கோபத்தில் இருக்காள்\nB. அம்மா மன்னிப்பு கேட்கிறாள்\nC. அம்மா ஆறுதல் சொன்னாள்\nD. அம்மா தண்டி கொட்டினாள்",
                    "C. அம்மா ஆறுதல் சொன்னாள்",
                ),
            ]
        else:
            examples = []
    else:  # latin
        instruction = (
            "Intha kelvikku badhil enna?\n"
            "Sariyaana option letter (A/B/C/D) um sariyaana optionil ulla badhil mattum kodukka vendum."
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    'Priya sonnaal, "Inniki saapadu romba nallaa irukku."',
                    "A. Priyavukku saapadu pidichirukku\nB. Priya saapidala\nC. Priya saapadu seidaal\nD. Priyavukku pasi illai",
                    "A. Priyavukku saapadu pidichirukku",
                ),
                (
                    'Rajan sonnaal, "Veliyil romba kulir irukku." Aanaa avan veliyil poganum.',
                    "A. Rajan veliyil pogamaatan\nB. Rajan veliyil poguvaan\nC. Rajanukku kulir theriyaadu\nD. Rajan veetilye irupaan",
                    "B. Rajan veliyil poguvaan",
                ),
                (
                    'Amma sonnaal, "Paravala, next time kavanam aa iru."',
                    "A. Amma kovathil irukaal\nB. Amma mannippu ketkiral\nC. Amma aarutal sonnaal\nD. Amma thandi kottinaal",
                    "C. Amma aarutal sonnaal",
                ),
            ]
        else:
            examples = []

    return instruction, examples


def nli_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    if script == "tamil":
        instruction = (
            "கொடுக்கப்பட்ட premise-க்கு கொடுக்கப்பட்ட hypothesis சரியானதா?\n"
            "தொடர்பு இந்த மூன்றில் எது என்று ஒரு வரியில் கொடுக்க வேண்டும்: Entailment, Contradiction, அல்லது Neutral."
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    "A: சாப்பாடு ready ஆச்சா?\nB: நான் இப்போ bazaar போனேன்.",
                    "சாப்பாடு ready ஆகியிருக்கு.",
                    "Contradiction",
                ),
                (
                    "A: நாளைக்கு விடுமுறை னு தெரியுமா?\nB: ஆமா, நான் காலையிலயே plan பண்றேன்.",
                    "B நாளைக்கு எதாவது செய்ய விரும்புகிறான்.",
                    "Entailment",
                ),
                (
                    "A: வெளியிலே மழை பெய்யுது.\nB: சரி.",
                    "B வெளியில் போவான்.",
                    "Neutral",
                ),
            ]
        else:
            examples = []
    else:  # latin
        instruction = (
            "Kodukkapattulla premisekku kodukkappatta hypothesis sariyaanatha?\n"
            "Thodarbu intha moondril ethu endru oru variyil kodukka vendum: Entailment, Contradiction, athava Neutral."
        )
        if prompt_style == "fewshot":
            examples = [
                (
                    "A: Saapadu ready aachaa?\nB: Naan ippo bazaar ponen.",
                    "Saapadu ready aagiyirukku.",
                    "Contradiction",
                ),
                (
                    "A: Naalaiku vidumuRai nu theriyumaa?\nB: Aamaa, naan kaalayilaye plan panren.",
                    "B naalaiku edhavadhu seiya viruppapadugiraan.",
                    "Entailment",
                ),
                (
                    "A: Veliyile mazhai peyyudhu.\nB: Sari.",
                    "B veliyile poguvaan.",
                    "Neutral",
                ),
            ]
        else:
            examples = []

    return instruction, examples


def translation_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    instruction = (
        "Translate the following Tamil text into natural, idiomatic English.\n"
        "Output only the translated text."
    )
    if prompt_style == "fewshot":
        examples = [
            ("Avanga onnu sernthu velai pannanga.", "They worked together."),
            ("Sandhaiyil pala vidhamaana porutkal kidaikkum.", "A wide variety of goods is available in the market."),
            ("Avan than vaakkai kaathu, samayathirku vandhaan.", "He kept his promise and arrived on time."),
        ]
    else:
        examples = []
    return instruction, examples
