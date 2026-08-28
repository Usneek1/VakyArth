# VakyArth Dataset

This directory contains the full **VakyArth** benchmark: human-authored pragmatics evaluation items across four Indic languages, released alongside our EMNLP paper *"VakyArth: Evaluating Pragmatic Competence in LLMs across Indic Languages."*

All items were written from scratch by native-speaker annotators (one per language, each with graduate-level NLP training) — nothing here is machine-translated or sourced from existing corpora.

## Coverage

| | Hindi | Punjabi | Tamil | Malayalam |
|---|---|---|---|---|
| Language family | Indo-Aryan | Indo-Aryan | Dravidian | Dravidian |
| Script | Devanagari | Gurmukhi | Tamil | Malayalam |

Each language is evaluated across **5 pragmatic phenomena**, and every phenomenon is instantiated as **3 task formats**:

**Phenomena**
- `deixis` — context-dependent reference (temporal, spatial, person, discourse deixis)
- `speech_acts` — utterances that perform actions (requests, refusals, indirect commands, blessings)
- `implicature` — meaning conveyed but not literally stated (sarcasm, hyperbole, idiom)
- `social_pragmatics` — kinship, register, gender norms, and politeness conventions
- `coherence` — discourse-level reasoning about how utterances relate within a passage

**Task formats**
- `mcqs.json` — multiple-choice question: pick the pragmatically correct interpretation from 4 options
- `nli.json` — natural language inference: label a premise/hypothesis pair as `entailment`, `contradiction`, or `neutral`
- `translation.json` — translate the source-language utterance into natural, idiomatic English

Most items are naturally code-mixed with English, reflecting how these languages are actually used in everyday digital communication (especially Hindi and Punjabi). All items are presented in Latin transliteration alongside native script, plus an English gloss.

## Directory layout

```
data/
├── Hindi/
│   ├── deixis/
│   │   ├── mcqs.json
│   │   ├── nli.json
│   │   └── translation.json
│   ├── speech_acts/
│   ├── implicature/
│   ├── social_pragmatics/
│   └── coherence/
├── Punjabi/        (same structure)
├── Tamil/          (same structure)
└── Malayalam/      (same structure)
```

`<Language>/<phenomenon>/<task>.json` — 4 languages × 5 phenomena × 3 tasks = 60 files.

## Item counts

| Language | Total items |
|---|---|
| Hindi | 212 |
| Punjabi | 125 |
| Tamil | 90 |
| Malayalam | 134 |
| **Total** | **561** |

Counts are summed across MCQ, NLI, and Translation items for all 5 phenomena. The dataset is still growing — these numbers, and the corresponding table in the paper, will be updated together before the camera-ready draft.

## Schema

Every file has a top-level `dataset` (name) and `version` field, plus an `items` list. Common fields across item types:

- `id` — unique item identifier, e.g. `hi_imp_mcq_001`
- `type` — one of `mcq`, `nli`, `translation`
- `phenomena` — list of fine-grained pragmatic tags, e.g. `["implicature", "sarcasm", "work-critique"]`
- `scripts` — the same content rendered in native script, Latin transliteration, and English

### MCQ (`mcqs.json`)

```json
{
  "id": "hi_imp_mcq_001",
  "type": "mcq",
  "phenomena": ["implicature", "sarcasm", "work-critique"],
  "scripts": {
    "devanagari": { "context": "...", "question": "...", "options": ["...", "...", "...", "..."], "answer": { "label": "B", "index": 1, "text": "..." } },
    "latin":      { "context": "...", "question": "...", "options": [...], "answer": {...} },
    "english":    { "context": "...", "question": "...", "options": [...], "answer": {...} },
    "explanation": "Sarcastic praise implies the report is poorly done.",
    "metadata": { "register": "colleague/student", "cultural_markers": ["sarcastic praise to critique quality of work"] }
  }
}
```

### NLI (`nli.json`)

```json
{
  "id": "hi_nli_001",
  "type": "nli",
  "phenomena": ["implicature", "metaphor", "weather-context"],
  "scripts": {
    "latin":       { "premise": [{ "speaker": "A", "utterance": "..." }, { "speaker": "B", "utterance": "..." }], "hypothesis": "..." },
    "devanagari":  { "premise": [...], "hypothesis": "..." },
    "english":     { "premise": [...], "hypothesis": "..." }
  },
  "label": "contradiction",
  "explanation": "B's statement is a metaphor for extreme heat, implying it's a bad idea to go out. This contradicts the hypothesis that B wants to go."
}
```

`premise` is either a list of speaker turns (single- or multi-party dialogue) or a plain string (a monologue/paragraph, used mainly for `coherence` items); `label` is one of `entailment`, `contradiction`, `neutral`, and is always top-level.

### Translation (`translation.json`)

```json
{
  "id": "hi_tr_001",
  "type": "translation",
  "phenomena": ["euphemism", "death"],
  "source": {
    "language": "hindi",
    "scripts": { "devanagari": "...", "latin": "..." }
  },
  "reference_translation": { "language": "english", "text": "His grandfather passed away last month." },
  "notes": "'Chal basna' is a euphemistic expression for dying, literally meaning 'departed' or 'left for heavenly abode'."
}
```

Each `translation.json` also carries a top-level `direction` field (e.g. `"hindi_to_english"`) and a `task_description`.

## License

TBD — see the top-level [README](../README.md) for release status.
