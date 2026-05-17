from typing import TypedDict
from langgraph.graph import StateGraph, END
class FloodlightState(TypedDict):
    spec_data: dict
    validation_passed: bool
def validate_specs(state: FloodlightState):
    required = ['IP Rating', 'Luminous Flux']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}
workflow = StateGraph(FloodlightState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()