from typing import TypedDict
from langgraph.graph import StateGraph, END

class InkjetWorkflowState(TypedDict):
    device_id: str
    material_compliance: bool
    validation_score: float

def validate_specs(state: InkjetWorkflowState):
    state['validation_score'] = 1.0 if state['device_id'] else 0.0
    return state

def check_compliance(state: InkjetWorkflowState):
    state['material_compliance'] = True
    return state

graph = StateGraph(InkjetWorkflowState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()