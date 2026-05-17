from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicrowaveState(TypedDict):
    model_number: str
    compliance_checked: bool
    safety_verified: bool

def validate_model(state: MicrowaveState):
    print(f'Validating model: {state["model_number"]}')
    return {'compliance_checked': True}

def verify_safety(state: MicrowaveState):
    print('Checking PSE/UL safety standards')
    return {'safety_verified': True}

graph = StateGraph(MicrowaveState)
graph.add_node('validate', validate_model)
graph.add_node('safety', verify_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()