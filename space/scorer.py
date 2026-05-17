import os
import re

import streamlit as st
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from prompting import build_contrast_prompt, load_contrast_examples

BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
LORA_ADAPTER = "salarion-witch/qwen-ielts-lora"
MAX_NEW_TOKENS = 400


def _hf_token():
    try:
        return st.secrets["HF_TOKEN"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("HF_TOKEN")


@st.cache_resource(show_spinner="Загрузка модели...")
def load_model():
    token = _hf_token()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, token=token, trust_remote_code=True)
    tokenizer.padding_side = "right"

    model_kwargs = {
        "pretrained_model_name_or_path": BASE_MODEL,
        "token": token,
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
    }

    if torch.cuda.is_available():
        from transformers import BitsAndBytesConfig

        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        model_kwargs["device_map"] = "auto"
    else:
        model_kwargs["torch_dtype"] = torch.float16
        model_kwargs["device_map"] = "cpu"

    base_model = AutoModelForCausalLM.from_pretrained(**model_kwargs)
    model = PeftModel.from_pretrained(base_model, LORA_ADAPTER, token=token)
    model.eval()
    return model, tokenizer


@st.cache_data
def _examples():
    return load_contrast_examples()


def _round_band(score):
    if score is None:
        return None
    return min(max(round(score * 2) / 2, 0), 9)


def _extract_scores(response):
    patterns = {
        "TR": r"TR[_\s]*Band:\s*(\d+(?:\.\d)?)",
        "CC": r"CC[_\s]*Band:\s*(\d+(?:\.\d)?)",
        "LR": r"LR[_\s]*Band:\s*(\d+(?:\.\d)?)",
        "GRA": r"GRA[_\s]*Band:\s*(\d+(?:\.\d)?)",
        "Overall": r"Overall[_\s]*Band:\s*(\d+(?:\.\d)?)",
    }
    scores = {}
    for criterion, pattern in patterns.items():
        match = re.search(pattern, response, re.IGNORECASE)
        scores[criterion] = _round_band(float(match.group(1))) if match else None

    if scores["Overall"] is None and all(scores[k] is not None for k in ("TR", "CC", "LR", "GRA")):
        avg = sum(scores[k] for k in ("TR", "CC", "LR", "GRA")) / 4
        scores["Overall"] = _round_band(avg)
    return scores


def _extract_explanation(response):
    match = re.search(r"Explanation:\s*(.+)", response, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else response.strip()


def _generate(model, tokenizer, essay, task):
    prompt = build_contrast_prompt(essay=essay, task=task, examples=_examples())
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            repetition_penalty=1.1,
        )

    return tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def score_essay(task, essay):
    if not task.strip() or not essay.strip():
        return {
            "status": "error",
            "scores": None,
            "overall_feedback": None,
            "error": "Task и Essay не должны быть пустыми.",
        }

    try:
        model, tokenizer = load_model()
        raw = _generate(model, tokenizer, essay.strip(), task.strip())
        scores = _extract_scores(raw)
        explanation = _extract_explanation(raw)

        criteria = ("TR", "CC", "LR", "GRA")
        if any(scores[k] is None for k in criteria):
            raise ValueError(f"Не удалось распарсить ответ модели: {raw[:300]}")

        total = scores["Overall"] or _round_band(sum(scores[k] for k in criteria) / 4)

        return {
            "status": "ok",
            "scores": {
                key: {"score": scores[key], "comment": f"Band {scores[key]}."}
                for key in criteria
            }
            | {"total": total},
            "overall_feedback": explanation,
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "scores": None,
            "overall_feedback": None,
            "error": str(exc),
        }
