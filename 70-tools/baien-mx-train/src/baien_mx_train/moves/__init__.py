"""Per-modality data loaders + encoder-forward stubs.

Each `<modality>.py` exposes `load_input(graft_row) -> torch.Tensor`
shaped `(B, n_input_tokens, output_dim)` ready for the modality's
projector.
"""
