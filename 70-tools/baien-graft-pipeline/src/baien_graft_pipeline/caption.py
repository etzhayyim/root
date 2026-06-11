"""Florence-2 captioner wrapper (uses MPS on Apple Silicon, CPU fallback)."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

MODEL_ID = "microsoft/Florence-2-large-ft"
DEFAULT_TASK = "<MORE_DETAILED_CAPTION>"


class FlorenceCaptioner:
    def __init__(self, model_id: str = MODEL_ID, device: str | None = None) -> None:
        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self.dtype = torch.float16 if device == "mps" else torch.float32
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.model = (
            AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=self.dtype, trust_remote_code=True)
            .to(device)
            .eval()
        )

    def caption(self, image_path: str | Path, task: str = DEFAULT_TASK) -> str:
        img = Image.open(image_path).convert("RGB")
        inputs = self.processor(text=task, images=img, return_tensors="pt").to(self.device, self.dtype)
        with torch.inference_mode():
            out = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=512,
                num_beams=3,
                do_sample=False,
            )
        raw = self.processor.batch_decode(out, skip_special_tokens=False)[0]
        parsed = self.processor.post_process_generation(raw, task=task, image_size=(img.width, img.height))
        return parsed.get(task, "").strip()
