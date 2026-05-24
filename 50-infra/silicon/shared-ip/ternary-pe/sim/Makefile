# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb + Verilator runner for ternary_pe.
#
# Requirements (open-source only):
#   - verilator (>= 5.020)
#   - cocotb    (>= 1.8)
#   - python3   (>= 3.10)
#
# Usage:
#   make sim

SIM            ?= verilator
TOPLEVEL_LANG  ?= verilog
EXTRA_ARGS     += --trace --trace-fst

VERILOG_SOURCES = $(PWD)/../rtl/ternary_pe.sv
TOPLEVEL        = ternary_pe
MODULE          = test_ternary_pe

include $(shell cocotb-config --makefiles)/Makefile.sim
