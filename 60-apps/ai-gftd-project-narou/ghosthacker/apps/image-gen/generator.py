"""Diffusers pipeline manager for local image generation on Apple Silicon."""

import io
import logging
import random
import time

import torch
from diffusers import StableDiffusionXLPipeline, LCMScheduler, EulerDiscreteScheduler
from PIL import Image

import config

logger = logging.getLogger(__name__)


class ImageGenerator:
    def __init__(self):
        self.pipe = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model_loaded = False
        self.load_time_ms = 0
        # LCM-LoRA state
        self._lcm_enabled = False
        self._original_scheduler_config = None
        # Progress tracking
        self._current_job_id: str | None = None
        self._current_step: int = 0
        self._total_steps: int = 0
        self._step_start_time: float = 0
        self._avg_step_time_ms: float = 0
        self._cancelled: bool = False

    def _step_callback(self, pipe, step_index, timestep, callback_kwargs):
        """Called after each denoising step for progress tracking."""
        self._current_step = step_index + 1
        elapsed = (time.time() - self._step_start_time) * 1000
        if self._current_step > 0:
            self._avg_step_time_ms = elapsed / self._current_step
        if self._cancelled:
            raise InterruptedError("Generation cancelled")
        return callback_kwargs

    def cancel_current(self):
        """Request cancellation of current generation."""
        self._cancelled = True

    @property
    def progress(self) -> dict:
        """Return current generation progress."""
        if not self._current_job_id:
            return {"generating": False}
        remaining = self._total_steps - self._current_step
        eta_ms = remaining * self._avg_step_time_ms if self._avg_step_time_ms > 0 else 0
        return {
            "generating": True,
            "job_id": self._current_job_id,
            "current_step": self._current_step,
            "total_steps": self._total_steps,
            "avg_step_time_ms": round(self._avg_step_time_ms, 1),
            "estimated_remaining_ms": round(eta_ms, 1),
        }

    def load_model(self):
        """Load the SDXL pipeline with MPS-optimized settings.

        Uses float32 because fp16 on MPS produces all-black images.
        Memory usage ~12GB which fits comfortably in M4 Mac 32GB.
        """
        logger.info("Loading model: %s (device=%s, dtype=float32)", config.MODEL_ID, self.device)
        start = time.time()

        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            config.MODEL_ID,
            torch_dtype=torch.float32,
            use_safetensors=True,
        )
        self.pipe.to(self.device)
        self.pipe.enable_attention_slicing()

        self.load_time_ms = int((time.time() - start) * 1000)
        self.model_loaded = True
        self._original_scheduler_config = self.pipe.scheduler.config
        logger.info("Model loaded in %d ms", self.load_time_ms)

    def enable_lcm(self):
        """Enable LCM-LoRA for fast generation (4 steps)."""
        if self._lcm_enabled:
            return
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        logger.info("Enabling LCM-LoRA: %s", config.LCM_LORA_ID)
        start = time.time()
        self.pipe.scheduler = LCMScheduler.from_config(self._original_scheduler_config)
        self.pipe.load_lora_weights(config.LCM_LORA_ID)
        self._lcm_enabled = True
        logger.info("LCM-LoRA enabled in %d ms", int((time.time() - start) * 1000))

    def disable_lcm(self):
        """Disable LCM-LoRA, revert to normal scheduler."""
        if not self._lcm_enabled:
            return
        logger.info("Disabling LCM-LoRA")
        self.pipe.unload_lora_weights()
        self.pipe.scheduler = EulerDiscreteScheduler.from_config(self._original_scheduler_config)
        self._lcm_enabled = False

    @property
    def lcm_enabled(self) -> bool:
        return self._lcm_enabled

    def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        width: int = config.DEFAULT_WIDTH,
        height: int = config.DEFAULT_HEIGHT,
        num_inference_steps: int = config.DEFAULT_STEPS,
        guidance_scale: float = config.DEFAULT_GUIDANCE_SCALE,
        seed: int | None = None,
    ) -> tuple[Image.Image, int, int]:
        """Generate an image from a text prompt.

        Returns:
            tuple of (PIL Image, seed used, generation time in ms)
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        if negative_prompt is None:
            negative_prompt = config.DEFAULT_NEGATIVE_PROMPT

        # Override steps & guidance for LCM mode
        if self._lcm_enabled:
            num_inference_steps = config.LCM_STEPS
            guidance_scale = config.LCM_GUIDANCE_SCALE

        # MPS requires CPU generator for reproducibility
        generator = torch.Generator(device="cpu").manual_seed(seed)

        logger.info(
            "Generating: %dx%d, steps=%d, cfg=%.1f, seed=%d, lcm=%s",
            width, height, num_inference_steps, guidance_scale, seed, self._lcm_enabled,
        )

        # Reset progress tracking
        self._current_step = 0
        self._total_steps = num_inference_steps
        self._avg_step_time_ms = 0
        self._cancelled = False
        self._step_start_time = time.time()

        start = time.time()

        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
            callback_on_step_end=self._step_callback,
        )
        image = result.images[0]

        gen_time_ms = int((time.time() - start) * 1000)
        logger.info("Generated in %d ms (seed=%d)", gen_time_ms, seed)

        return image, seed, gen_time_ms

    def generate_with_style(
        self,
        prompt: str,
        style: str = "cinematic_sketch",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
    ) -> tuple[Image.Image, int, int]:
        """Generate an image with a predefined style preset.

        Returns:
            tuple of (PIL Image, seed used, generation time in ms)
        """
        preset = config.STYLE_PRESETS.get(style, config.STYLE_PRESETS["cinematic_sketch"])
        full_prompt = preset["prefix"] + prompt + preset["suffix"]

        dims = config.ASPECT_RATIOS.get(aspect_ratio, config.ASPECT_RATIOS["16:9"])

        return self.generate(
            prompt=full_prompt,
            width=dims[0],
            height=dims[1],
            seed=seed,
        )


def image_to_base64(image: Image.Image, fmt: str = "PNG") -> str:
    """Convert PIL Image to base64 data URL string."""
    import base64

    buf = io.BytesIO()
    image.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    mime = f"image/{fmt.lower()}"
    return f"data:{mime};base64,{b64}"
