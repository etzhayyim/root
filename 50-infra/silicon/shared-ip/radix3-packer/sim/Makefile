# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb + Verilator runner for radix3_decoder.
#
# Requirements (open-source only):
#   - verilator (>= 5.020)
#   - cocotb    (>= 1.8; tested on 2.0.1)
#   - python3   (>= 3.10)
#
# Usage:
#   make sim

SIM            ?= verilator
TOPLEVEL_LANG  ?= verilog
EXTRA_ARGS     += --trace --trace-fst

VERILOG_SOURCES = $(PWD)/../rtl/radix3_decoder.sv
TOPLEVEL        = radix3_decoder
COCOTB_TEST_MODULES = test_radix3_decoder

include $(shell cocotb-config --makefiles)/Makefile.sim
