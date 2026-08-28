"""HuggingFace model runner for language model inference.

This module provides a wrapper around HuggingFace transformers for loading and running
language models. It handles tokenization, model loading, and text generation.
"""
import os
import shutil
import torch
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM

load_dotenv()

HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN")
if HUGGING_FACE_TOKEN is None:
    raise ValueError("HUGGING_FACE_TOKEN environment variable is not set.")


class HFModelRunner:
    def __init__(self, model_name: str):
        self.model_name = model_name
        cache_dir = f"/tmp/hf_{os.getpid()}"

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            padding_side="left",
            truncation_side="left",
            token=HUGGING_FACE_TOKEN,
            trust_remote_code=True,
            cache_dir=cache_dir,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            token=HUGGING_FACE_TOKEN,
            cache_dir=cache_dir,
        )

        # Free disk cache — model is now in GPU memory
        shutil.rmtree(cache_dir, ignore_errors=True)
        self.model.eval()

    def generate(self, prompt: str, max_new_tokens: int = 128, temperature: float = 0.2) -> str:
        if "Qwen3" in self.model_name:
            prompt = "/no_think\n" + prompt
        enc = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        prompt_len = enc["input_ids"].shape[1]

        with torch.no_grad():
            out_ids = self.model.generate(
                **enc,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                num_beams=1,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Slice at token level — avoids prompt string mismatch
        new_ids = out_ids[0][prompt_len:]
        return self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()
