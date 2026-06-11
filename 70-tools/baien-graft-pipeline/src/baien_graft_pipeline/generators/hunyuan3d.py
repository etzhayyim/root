"""ComfyUI workflow factory for Hunyuan3D-2 mesh generation."""

from typing import Any


def hunyuan3d_workflow(image_name: str, output_prefix: str, seed: int = 42) -> dict[str, Any]:
    return {
        "prompt": {
            "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
            "2": {
                "class_type": "Hy3DModelLoader",
                "inputs": {
                    "model": "hunyuan3d-dit-v2-0-fp16.safetensors",
                    "attention_mode": "sdpa",
                    "cublas_ops": False,
                },
            },
            "3": {
                "class_type": "Hy3DGenerateMesh",
                "inputs": {
                    "pipeline": ["2", 0],
                    "image": ["1", 0],
                    "guidance_scale": 5.5,
                    "steps": 30,
                    "seed": seed,
                },
            },
            "4": {
                "class_type": "Hy3DVAEDecode",
                "inputs": {
                    "vae": ["2", 1],
                    "latents": ["3", 0],
                    "box_v": 1.01,
                    "octree_resolution": 384,
                    "num_chunks": 8000,
                    "mc_level": 0.0,
                    "mc_algo": "mc",
                    "enable_flash_vdm": True,
                    "force_offload": True,
                },
            },
            "5": {
                "class_type": "Hy3DExportMesh",
                "inputs": {
                    "trimesh": ["4", 0],
                    "filename_prefix": f"baien-graft/batch/{output_prefix}",
                    "file_format": "glb",
                    "save_file": True,
                },
            },
        }
    }
