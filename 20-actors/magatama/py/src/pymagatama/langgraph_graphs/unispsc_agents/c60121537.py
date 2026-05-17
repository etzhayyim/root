from langgraph.graph import StateGraph, END
from typing import TypedDict
class DipPenState(TypedDict):
    spec_completed: bool
    nib_material: str
    validation_passed: bool
def validate_nib(state: DipPenState):
    state['validation_passed'] = bool(state.get('nib_material'))
    return 'check_success' if state['validation_passed'] else 'error'
def finalize_procurement(state: DipPenState):
    state['spec_completed'] = True
    return 'end'
graph = StateGraph(DipPenState)
graph.add_node('validate', validate_nib)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()