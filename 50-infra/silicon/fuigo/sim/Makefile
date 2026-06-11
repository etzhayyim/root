# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb + Verilator runner for fuigo RTL.
#   make sim     # forward-path integration (shared ternary-pe IP)

SIM            ?= verilator
TOPLEVEL_LANG  ?= verilog
EXTRA_ARGS     += --trace --trace-fst

SHARED_IP = $(PWD)/../../shared-ip
IW        = $(PWD)/../../iwakura/rtl

VERILOG_SOURCES     = $(SHARED_IP)/ternary-pe/rtl/ternary_pe.sv \
                      $(IW)/pe_array.sv \
                      $(PWD)/../rtl/fuigo_top.sv
TOPLEVEL            = fuigo_top
COCOTB_TEST_MODULES = test_fuigo_top

include $(shell cocotb-config --makefiles)/Makefile.sim
