from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class WindowFrameState(TypedDict):
    specs: dict
    validation_log: List[str]
    is_approved: bool

def validate_specs(state: WindowFrameState):
    log = []
    if state['specs'].get('thermal_transmittance', 0) > 2.0:
        log.append('High thermal transmittance: energy efficiency check needed.')
    return {'validation_log': log}

def approval_node(state: WindowFrameState):
    return {'is_approved': len(state['validation_log']) == 0}

builder = StateGraph(WindowFrameState)
builder.add_node('validate', validate_specs)
builder.add_node('approve', approval_node)
builder.set_entry_point('validate')
builder.add_edge('validate', 'approve')
builder.add_edge('approve', END)
graph = builder.compile()
