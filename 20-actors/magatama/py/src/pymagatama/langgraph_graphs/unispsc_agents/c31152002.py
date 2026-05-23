from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BarbedWireState(TypedDict):
    specs: dict
    approved: bool
    safety_check: bool

def validate_specs(state: BarbedWireState):
    is_valid = 'wire_gauge' in state['specs'] and state['specs']['tensile_strength'] > 400
    return {'approved': is_valid}

def safety_compliance(state: BarbedWireState):
    return {'safety_check': True}

graph = StateGraph(BarbedWireState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
