from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SoftwareProcurementState(TypedDict):
    requirements: dict
    validation_results: List[str]
    is_approved: bool

def validate_tech_specs(state: SoftwareProcurementState):
    # Simulate validation logic for software requirements
    state['validation_results'].append('API integration checked')
    state['is_approved'] = True
    return state

graph = StateGraph(SoftwareProcurementState)
graph.add_node('validate', validate_tech_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()