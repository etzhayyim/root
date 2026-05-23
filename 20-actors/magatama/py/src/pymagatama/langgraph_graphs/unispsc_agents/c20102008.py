from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MiningState(TypedDict):
    part_id: str
    spec_data: dict
    validation_status: str
    compliance_risk: list[str]

def validate_material(state: MiningState) -> MiningState:
    if state['spec_data'].get('hardness', 0) < 50:
        state['validation_status'] = 'FAIL_LOW_HARDNESS'
    else:
        state['validation_status'] = 'PASS'
    return state

def check_export_control(state: MiningState) -> MiningState:
    state['compliance_risk'] = ['dual-use-export-control']
    return state

builder = StateGraph(MiningState)
builder.add_node('validate', validate_material)
builder.add_node('compliance', check_export_control)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
