from langgraph.graph import StateGraph, END
from typing import TypedDict
class BedState(TypedDict):
    spec_requirements: dict
    validation_passed: bool
def validate_medical_specs(state: BedState):
    required = ['medical_device_certification', 'material_non_toxicity']
    passed = all(k in state['spec_requirements'] for k in required)
    return {**state, 'validation_passed': passed}
def check_safety_standards(state: BedState):
    return {**state, 'validation_passed': state.get('validation_passed', False) and state['spec_requirements'].get('load_capacity_kg', 0) > 0}
graph = StateGraph(BedState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('safety', check_safety_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()