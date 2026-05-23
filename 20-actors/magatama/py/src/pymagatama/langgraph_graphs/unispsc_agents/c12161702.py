from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_log: Annotated[list[str], operator.add]
    status: str

def validate_purity(state: MetalPowderState):
    purity = state['spec_data'].get('purity', 0)
    if purity < 99.9:
        return {'validation_log': ['Purity level insufficient'], 'status': 'REJECTED'}
    return {'validation_log': ['Purity validated'], 'status': 'PASSED'}

def export_control_check(state: MetalPowderState):
    if state['spec_data'].get('dual_use', False):
        return {'validation_log': ['Dual-use control triggered'], 'status': 'REVIEW_REQUIRED'}
    return {'validation_log': ['Export control cleared'], 'status': 'PASSED'}

builder = StateGraph(MetalPowderState)
builder.add_node('validate', validate_purity)
builder.add_node('control', export_control_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'control')
builder.add_edge('control', END)
graph = builder.compile()
