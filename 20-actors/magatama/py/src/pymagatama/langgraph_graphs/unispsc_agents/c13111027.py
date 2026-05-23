from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PetroState(TypedDict):
    batch_id: str
    composition_data: dict
    validation_checks: List[str]
    approved: bool

def validate_composition(state: PetroState):
    checks = []
    if state['composition_data'].get('sulfur', 0) < 0.5:
        checks.append('sulfur_limit_pass')
    return {'validation_checks': checks}

def safety_routing(state: PetroState):
    if 'sulfur_limit_pass' in state['validation_checks']:
        return 'approve'
    return 'reject'

graph = StateGraph(PetroState)
graph.add_node('validate', validate_composition)
graph.add_edge('validate', 'approve')
graph.add_node('approve', lambda s: {'approved': True})
graph.set_entry_point('validate')
graph.add_edge('approve', END)
app = graph.compile()
