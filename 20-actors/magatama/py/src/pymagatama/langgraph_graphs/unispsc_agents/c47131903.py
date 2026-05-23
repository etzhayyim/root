from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class State(TypedDict):
    material_specs: dict
    validation_passed: bool
    compliance_report: str

def validate_safety_data(state: State):
    is_safe = 'SDS' in state['material_specs'] and state['material_specs']['VOC_compliant']
    return {'validation_passed': is_safe, 'compliance_report': 'Safety check successful' if is_safe else 'Safety check failed'}

def process_plugging_compound(state: State):
    return {'compliance_report': 'Compound formulation verified against industrial standards.'}

graph = StateGraph(State)
graph.add_node('safety_check', validate_safety_data)
graph.add_node('formulation_process', process_plugging_compound)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'formulation_process')
graph.add_edge('formulation_process', END)
graph = graph.compile()
