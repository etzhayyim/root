from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validation_result: bool
    compliance_flag: bool

def validate_specs(state: ExtrusionState):
    # Logic to verify alloy composition and tolerance constraints
    valid = all(k in state['specs'] for k in ['alloy', 'tolerance'])
    return {'validation_result': valid}

def check_export_compliance(state: ExtrusionState):
    # Logic for dual-use export control screening
    return {'compliance_flag': True}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
