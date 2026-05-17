from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompassState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: CompassState):
    # Precision validation logic for directional instruments
    accuracy = state['specs'].get('accuracy', 0)
    if accuracy < 0.5: 
        return {'validation_passed': True}
    return {'validation_passed': False}

def check_compliance(state: CompassState):
    # Dual-use regulatory compliance check
    return {'compliance_report': 'ITAR/EAR clearance required for specified models'}

graph = StateGraph(CompassState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

app = graph.compile()