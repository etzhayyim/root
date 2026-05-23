from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class PumpPartState(TypedDict):
    part_specs: dict
    validation_checks: List[str]
    approved: bool
def validate_specs(state: PumpPartState):
    errors = []
    if not state['part_specs'].get('material'): errors.append('Missing material')
    if not state['part_specs'].get('pressure_rating'): errors.append('Missing pressure rating')
    return {'validation_checks': errors, 'approved': len(errors) == 0}
def route_step(state: PumpPartState):
    return 'approved' if state['approved'] else 'rejected'
graph = StateGraph(PumpPartState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
