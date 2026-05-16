#!/usr/bin/env python3
"""LoRA fine-tune Qwen3-VL-8B on UNSPSC commodity generation task using MLX.

Usage:
  python lora-finetune.py [--epochs 10] [--batch-size 1] [--lora-rank 16]

Requires: mlx, mlx-lm (pip install mlx mlx-lm)
Hardware: Apple Silicon M4 32GB
"""
import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="LoRA fine-tune for UNSPSC generation")
    parser.add_argument("--model", default="Qwen/Qwen3-VL-8B", help="Base model (HuggingFace ID)")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs (default: 20, small dataset needs more)")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size (1 for 32GB)")
    parser.add_argument("--lora-rank", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Learning rate")
    parser.add_argument("--output", default=None, help="Output directory for adapters")
    args = parser.parse_args()

    training_dir = os.path.dirname(os.path.abspath(__file__))
    if args.output is None:
        args.output = os.path.join(training_dir, "adapters")

    train_file = os.path.join(training_dir, "train.jsonl")
    valid_file = os.path.join(training_dir, "valid.jsonl")

    if not os.path.exists(train_file):
        print("ERROR: train.jsonl not found. Run build-dataset.py first.")
        sys.exit(1)

    # Count examples
    with open(train_file) as f:
        n_train = sum(1 for _ in f)
    with open(valid_file) as f:
        n_valid = sum(1 for _ in f)
    print(f"Dataset: {n_train} train, {n_valid} valid examples")

    # Calculate iters
    iters_per_epoch = max(1, n_train // args.batch_size)
    total_iters = iters_per_epoch * args.epochs
    val_batches = max(1, n_valid // args.batch_size)

    print(f"Config: rank={args.lora_rank}, lr={args.learning_rate}, epochs={args.epochs}")
    print(f"Iters: {total_iters} total ({iters_per_epoch}/epoch × {args.epochs} epochs)")
    print(f"Output: {args.output}")
    print()

    config_path = os.path.join(training_dir, "lora-config.yaml")

    # mlx_lm lora CLI (new syntax)
    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", args.model,
        "--train",
        "--data", training_dir,
        "--adapter-path", args.output,
        "--iters", str(total_iters),
        "--batch-size", str(args.batch_size),
        "--num-layers", "16",
        "--learning-rate", str(args.learning_rate),
        "--val-batches", str(val_batches),
        "--steps-per-eval", str(iters_per_epoch),
        "--steps-per-report", str(max(1, iters_per_epoch // 5)),
        "--save-every", str(iters_per_epoch * 5),
        "--max-seq-length", "4096",
        "--grad-checkpoint",
        "-c", config_path,
    ]

    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(cmd, cwd=training_dir)
    if result.returncode != 0:
        print(f"\nERROR: Training failed with code {result.returncode}")
        sys.exit(1)

    print(f"\nDone! Adapters saved to: {args.output}")
    print(f"\nTo test inference:")
    print(f"  python -m mlx_lm.generate \\")
    print(f"    --model {args.model} \\")
    print(f"    --adapter-path {args.output} \\")
    print(f'    --prompt "Generate UNSPSC commodity component: 51101501 Aspirin"')
    print(f"\nTo fuse adapters into model:")
    print(f"  python -m mlx_lm.fuse \\")
    print(f"    --model {args.model} \\")
    print(f"    --adapter-path {args.output} \\")
    print(f"    --save-path {os.path.join(training_dir, 'fused-model')}")


if __name__ == "__main__":
    main()
