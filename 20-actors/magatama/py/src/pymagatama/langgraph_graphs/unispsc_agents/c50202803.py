from langgraph.graph import StateGraph, END
from typing import TypedDict
class MangoState(TypedDict):
    brix: float
    ph: float
    safety_verified: bool
    approved: bool
def validate_quality(state: MangoState):
    if 25.0 <= state['brix'] <= 35.0 and 3.0 <= state['ph'] <= 4.5:
        return {'safety_verified': True}
    return {'safety_verified': False}
def finalize_order(state: MangoState):
    return {'approved': state['safety_verified']}
graph = StateGraph(MangoState)
graph.add_node('validate', validate_quality)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()