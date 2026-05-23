from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OdorControlState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: OdorControlState):
    errors = []
    if state['spec_data'].get('Odor_Removal_Efficiency_Percent', 0) < 95:
        errors.append('Efficiency threshold below minimum requirement')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: OdorControlState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(OdorControlState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
