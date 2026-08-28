"""
Malayalam Language Prompt Instruction
"""
def mcq_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    instruction = (
        "Ee chodyathinulla utharam enthaanu?\n"
        "Option letter (A/B/…) um shariyaaya utharathinte poornna vaachakavum maathram nalkuka."
    )
    if prompt_style == "fewshot":
        examples = [
            (
                'Priya paranju, "Innu sadhyam valare nannayitundu."',
                "A. Priyakku sadhyam ishtapettu\nB. Priya sadhyam kazhichilla\nC. Priya sadhyam undaakki\nD. Priyakku vishakkunilla",
                "A. Priyakku sadhyam ishtapettu",
            ),
            (
                'Rajan paranju, "Purathe valare thanuppaanu." Ennaalu avan purathe pokkanam.',
                "A. Rajan purathe pokilla\nB. Rajan purathe pokum\nC. Rajanu thanupp anubhavappedunilla\nD. Rajan veetil nikkunam",
                "B. Rajan purathe pokum",
            ),
            (
                'Amma paranju, "Saaramilla, aduthu thavana shraddhikkanam."',
                "A. Amma deshyathilaanu\nB. Amma maappu chodichu\nC. Amma aashwasippichu\nD. Amma shikshichu",
                "C. Amma aashwasippichu",
            ),
        ]
    else:
        examples = []
    return instruction, examples


def nli_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    # Native-script (Malayalam) instructions not yet authored; falls back to latin for all scripts.
    instruction = (
        "Thannirukkunna parisarathinu anumaanam uchithamaano?\n"
        "Bandhathe ithilonnaayi adayaalappeduthuka: Entailment, Contradiction, athava Neutral."
    )
    if prompt_style == "fewshot":
        examples = [
            (
                "A: Sadhyam ready aayittundo?\nB: Njaan ippol bazaril poyi.",
                "Sadhyam ready aayittundu.",
                "Contradiction",
            ),
            (
                "A: Naalae avadhi aanennu ariyaamo?\nB: Athe, njaan raavileyE plan cheyyunnu.",
                "B naalae enthenkilum cheyyaan aagrahikkunnu.",
                "Entailment",
            ),
            (
                "A: Purathe mazha peyyunnu.\nB: Ente.",
                "B purathe pokum.",
                "Neutral",
            ),
        ]
    else:
        examples = []
    return instruction, examples


def translation_instruction(category: str, prompt_style: str, script: str = "latin") -> tuple:
    # Native-script (Malayalam) instructions not yet authored; falls back to latin for all scripts.
    instruction = (
        "Thaazhe koduthirikkunna Malayalam text Englishilekku paribhasha cheyyuka.\n"
        "Outputil translated text maathrame kaanikkuka."
    )
    if prompt_style == "fewshot":
        examples = [
            ("Avare koode cheythu pani cheythu.", "They worked together."),
            ("Chantayil vividha saadhananngal labhikkum.", "A wide variety of goods is available in the market."),
            ("Avan vaakku paalikkukayum samayam thavanee ethukayum cheythu.", "He kept his promise and arrived on time."),
        ]
    else:
        examples = []
    return instruction, examples
