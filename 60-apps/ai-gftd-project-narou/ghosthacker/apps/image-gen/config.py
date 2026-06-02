"""Configuration for the local image generation service."""

# Model settings
MODEL_ID = "cagliostrolab/animagine-xl-4.0"
VAE_ID = "madebyollin/sdxl-vae-fp16-fix"

# Default generation parameters
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768
DEFAULT_STEPS = 28
DEFAULT_GUIDANCE_SCALE = 7.0
DEFAULT_NEGATIVE_PROMPT = (
    "low quality, worst quality, blurry, deformed, distorted, "
    "disfigured, bad anatomy, watermark, text, signature, "
    "extra fingers, mutated hands, poorly drawn face"
)

# Style presets matching Go server's image_generation.go
STYLE_PRESETS = {
    "cinematic_sketch": {
        "prefix": (
            "Cinematic storyboard thumbnail sketch, rough compositional guide "
            "for animators, gestural figures with simplified facial features, "
            "focus on camera framing staging and body language, "
            "manga panel layout reference. "
        ),
        "suffix": (
            ". Rough sketch aesthetic with loose confident linework, "
            "emphasis on lighting direction and silhouette shapes, "
            "atmospheric mood indicators, faces suggested through simple shapes "
            "rather than detailed features, director's visual notes style, "
            "monochrome with screen tones, cinematic composition."
        ),
    },
    "character_avatar": {
        "prefix": (
            "Professional character portrait, headshot, "
            "Mai Yoneyama illustrator style, High-End Webtoon Aesthetic, "
            "Fine Line Art, Modern Manga Style, clean background. "
        ),
        "suffix": (
            ". Sharp focus on face and expressive eyes, intricate iris detail, "
            "consistent facial features, clean white background, "
            "high resolution, 8k."
        ),
    },
}

# Aspect ratio presets (768px base)
ASPECT_RATIOS = {
    "16:9": (768, 432),   # multiples of 8
    "9:16": (432, 768),
    "1:1": (768, 768),
    "4:3": (768, 576),
    "3:4": (576, 768),
    "3:2": (768, 512),
    "2:3": (512, 768),
}

# LCM-LoRA acceleration settings
LCM_LORA_ID = "latent-consistency/lcm-lora-sdxl"
LCM_STEPS = 4
LCM_GUIDANCE_SCALE = 1.5

# Server settings
HOST = "0.0.0.0"
PORT = 8100
