from typing import TypedDict
from langgraph.graph import StateGraph, END
class UreteralState(TypedDict):
    spec_data: dict
    validated: bool
def validate_medical_spec(state: UreteralState):
    required = ['Sterility Certification', 'Regulatory Approval (FDA/CE/PMDA)']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state
graph = StateGraph(UreteralState)
graph.add_node('validate', validate_medical_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
