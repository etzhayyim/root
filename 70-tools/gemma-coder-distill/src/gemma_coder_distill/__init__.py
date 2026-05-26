"""gemma-coder-distill — LangGraph ReAct loop for gemma3:4b LangGraph-coding adaptation.

Per ADR-2605250400. Trainer: peft+trl direct (Unsloth fallback gate-1 probe
2026-05-25 confirmed Windows ROCm unsupported, see 90-docs/baien/probe_unsloth_rocm.json).

Mirrors baien-distill structure but specialised for gemma-3 architecture and
LangGraph-coding bench (70-tools/scripts/bench/langgraph-coding/).
"""
__version__ = "0.1.0"
