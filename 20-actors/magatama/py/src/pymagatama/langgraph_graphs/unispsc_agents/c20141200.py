from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MiningPartsState(TypedDict):
    part_id: str
    spec_compliance: bool
    safety_check: bool
    approval_status: str

def validate_specs(state: MiningPartsState):
    print(f'Validating specs for {state[\'part_id\']}')
    return {'spec_compliance': True}

def safety_audit(state: MiningPartsState):
    print('Performing high-value/safety compliance audit')
    return {'safety_check': True}

builder = StateGraph(MiningPartsState)
builder.add_node('specs', validate_specs)
builder.add_node('safety', safety_audit)
builder.add_edge('specs', 'safety')
builder.set_entry_point('specs')
builder.add_edge('safety', END)
graph = builder.compile()