from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: TubeState):
    is_valid = state['spec_data'].get('pressure_rating', 0) > 0
    return {'validation_passed': is_valid}

def generate_compliance(state: TubeState):
    report = 'Compliance confirmed for bonded assembly' if state['validation_passed'] else 'Compliance failed'
    return {'compliance_report': report}

graph = StateGraph(TubeState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()