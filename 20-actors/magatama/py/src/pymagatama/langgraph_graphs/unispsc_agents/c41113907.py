from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PorosityState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: PorosityState):
    errors = []
    if not state['spec_data'].get('max_pressure'):
        errors.append('Missing maximum pressure specification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def export_control_check(state: PorosityState):
    # Dual-use export control logic placeholder
    return {'approved': state['approved']}

graph = StateGraph(PorosityState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()