from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SatelliteState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: SatelliteState):
    errors = []
    if 'frequency' not in state['spec_data']:
        errors.append('Missing frequency input')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def export_control_check(state: SatelliteState):
    # Integrate with EAR/ITAR lookup logic
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(SatelliteState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
app = graph.compile()
