# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb + Verilator runner for iwakura RTL modules.
#
# Requirements (open-source only):
#   - verilator (>= 5.020; tested on 5.048)
#   - cocotb    (>= 1.8; tested on 2.0.1)
#   - python3   (>= 3.10)
#
# Usage:
#   make sim                          # default: pe_array (4×4)
#   make sim DUT=pe_array             # ternary matrix-vector engine
#   make sim DUT=pe_array_cg          # same, CLOCK_GATE=1 (zero-skip gating)
#   make sim DUT=zero_skip_dispatcher # clock-gate mask + BitNet power stat
#   make sim DUT=sram_scratch         # behavioural on-die SRAM
#   make sim DUT=lpddr5x_ctrl         # behavioural DRAM ctrl + radix-3 unpack
#   make sim DUT=iwakura_top          # integrated compute-tile smoke
#
# NOTE: the selector is `DUT`, not `MODULE` — `MODULE` is reserved by cocotb
# for the Python test module name (deprecated alias of COCOTB_TEST_MODULES).

SIM            ?= verilator
TOPLEVEL_LANG  ?= verilog
EXTRA_ARGS     += --trace --trace-fst

SHARED_IP = $(PWD)/../../shared-ip

# ── module selection ────────────────────────────────────────────────────────
DUT ?= pe_array

ifeq ($(DUT),pe_array)
  VERILOG_SOURCES     = $(SHARED_IP)/ternary-pe/rtl/ternary_pe.sv $(PWD)/../rtl/pe_array.sv
  TOPLEVEL            = pe_array
  COCOTB_TEST_MODULES = test_pe_array_4x4
endif

# Clock-gated variant: same pe_array elaborated with -GCLOCK_GATE=1, plus the
# zero_skip_dispatcher it wires in. Proves bit-identical results + write savings.
ifeq ($(DUT),pe_array_cg)
  VERILOG_SOURCES     = $(SHARED_IP)/ternary-pe/rtl/ternary_pe.sv \
                        $(PWD)/../rtl/zero_skip_dispatcher.sv \
                        $(PWD)/../rtl/pe_array.sv
  TOPLEVEL            = pe_array
  COCOTB_TEST_MODULES = test_pe_array_clockgate
  EXTRA_ARGS         += -GCLOCK_GATE=1
endif

ifeq ($(DUT),zero_skip_dispatcher)
  VERILOG_SOURCES     = $(PWD)/../rtl/zero_skip_dispatcher.sv
  TOPLEVEL            = zero_skip_dispatcher
  COCOTB_TEST_MODULES = test_zero_skip_dispatcher
endif

ifeq ($(DUT),sram_scratch)
  VERILOG_SOURCES     = $(PWD)/../rtl/memory/sram_scratch.sv
  TOPLEVEL            = sram_scratch
  COCOTB_TEST_MODULES = test_sram_scratch
endif

ifeq ($(DUT),lpddr5x_ctrl)
  VERILOG_SOURCES     = $(SHARED_IP)/radix3-packer/rtl/radix3_decoder.sv \
                        $(PWD)/../rtl/memory/lpddr5x_ctrl.sv
  TOPLEVEL            = lpddr5x_ctrl
  COCOTB_TEST_MODULES = test_lpddr5x_ctrl
endif

ifeq ($(DUT),iwakura_top)
  VERILOG_SOURCES     = $(SHARED_IP)/ternary-pe/rtl/ternary_pe.sv \
                        $(PWD)/../rtl/pe_array.sv \
                        $(PWD)/../rtl/zero_skip_dispatcher.sv \
                        $(PWD)/../rtl/iwakura_top.sv
  TOPLEVEL            = iwakura_top
  COCOTB_TEST_MODULES = test_iwakura_top
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
