from typing import TypedDict
from langgraph.graph import StateGraph, END

class StandState(TypedDict):
    material: str
    max_weight: float
    status: str

def validate_load_capacity(state: StandState):
    if state['max_weight'] < 2.0:
        return {'status': 'FAILED_CAPACITY'}
    return {'status': 'PASSED_CAPACITY'}

def finalize_spec(state: StandState):
    return {'status': 'READY_FOR_RFQ'}

graph = StateGraph(StandState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('finalize', finalize_spec)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
