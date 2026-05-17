from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MassSpecState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: MassSpecState):
    errors = []
    if 'resolution_power' not in state['specs']: errors.append('Resolution power missing')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_export_control(state: MassSpecState):
    # Mock logic for dual-use verification
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(MassSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
# Note: This represents the structural compile-ready layout