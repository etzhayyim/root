from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitState(TypedDict):
    kit_id: str
    specs_verified: bool
    safety_check: bool

def validate_specs(state: KitState):
    print(f'Validating specs for {state["kit_id"]}')
    return {'specs_verified': True}

def conduct_safety_audit(state: KitState):
    print(f'Conducting safety audit for {state["kit_id"]}')
    return {'safety_check': True}

graph = StateGraph(KitState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', conduct_safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
