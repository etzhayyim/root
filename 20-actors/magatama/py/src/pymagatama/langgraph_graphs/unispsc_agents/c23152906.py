from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_laser_safety(state: WeldingGraphState):
    errors = []
    if state['specs'].get('wattage_output', 0) > 5000:
        errors.append('High-power laser classification required')
    return {'validation_errors': errors}

def determine_compliance(state: WeldingGraphState):
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_laser_safety)
graph.add_node('compliance', determine_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()