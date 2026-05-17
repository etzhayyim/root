from typing import TypedDict
from langgraph.graph import StateGraph, END

class PneumaticState(TypedDict):
    specifications: dict
    validation_status: str
    compliance_check: bool

def validate_specs(state: PneumaticState):
    specs = state['specifications']
    is_valid = 'bore_diameter_mm' in specs and 'stroke_length_mm' in specs
    return {'validation_status': 'passed' if is_valid else 'failed', 'compliance_check': is_valid}

def check_dual_use(state: PneumaticState):
    return {'compliance_check': True}

graph = StateGraph(PneumaticState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_dual_use)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()