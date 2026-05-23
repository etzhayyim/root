from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MachineSpecs(TypedDict):
    force: float
    thickness: float
    safety_certs: List[str]
    approved: bool

def validate_specs(state: MachineSpecs):
    if state['force'] > 0 and state['thickness'] > 0:
        state['approved'] = True
    return state

builder = StateGraph(MachineSpecs)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
