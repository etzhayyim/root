from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RescueBoatState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_solas(state: RescueBoatState):
    errors = []
    if not state['specs'].get('solas_compliant'):
        errors.append('Missing SOLAS compliance certificate')
    return {'validation_errors': errors}

def check_hull_integrity(state: RescueBoatState):
    if state['specs'].get('hull_material') not in ['aluminum', 'fiberglass', 'steel']:
        return {'validation_errors': state['validation_errors'] + ['Invalid hull material']}
    return {}

graph = StateGraph(RescueBoatState)
graph.add_node('validate_solas', validate_solas)
graph.add_node('check_hull', check_hull_integrity)
graph.set_entry_point('validate_solas')
graph.add_edge('validate_solas', 'check_hull')
graph.add_edge('check_hull', END)

graph = graph.compile()