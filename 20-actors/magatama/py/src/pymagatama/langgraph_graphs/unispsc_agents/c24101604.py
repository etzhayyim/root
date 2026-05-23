from typing import TypedDict
from langgraph.graph import StateGraph
class LiftProcurementState(TypedDict):
    load_capacity: float
    has_safety_certification: bool
    approved: bool
def validate_specs(state: LiftProcurementState):
    state['approved'] = state['load_capacity'] > 0 and state['has_safety_certification']
    return state
graph = StateGraph(LiftProcurementState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.set_finish_point('validation')
graph = graph.compile()
