from typing import TypedDict
from langgraph.graph import StateGraph, END

class RehabTreadmillState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_specs(state: RehabTreadmillState):
    required = ['medical_device_certification', 'emergency_stop_mechanism']
    results = [key in state['spec_data'] for key in required]
    return {'validation_results': results, 'is_approved': all(results)}

graph = StateGraph(RehabTreadmillState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
