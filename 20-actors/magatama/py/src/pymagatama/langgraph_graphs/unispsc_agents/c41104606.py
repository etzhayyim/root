from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    temp_profile: dict
    compliance_check: bool
    safety_interlock: bool

def validate_specs(state: FurnaceState):
    if state['temp_profile'].get('max_temp', 0) > 1800:
        return {'compliance_check': False}
    return {'compliance_check': True}

def safety_audit(state: FurnaceState):
    return {'safety_interlock': True}

graph = StateGraph(FurnaceState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
