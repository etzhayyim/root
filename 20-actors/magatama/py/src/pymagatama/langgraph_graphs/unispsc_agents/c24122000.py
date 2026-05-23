from typing import TypedDict
from langgraph.graph import StateGraph, END

class BottleState(TypedDict):
    capacity: float
    material: str
    is_compliant: bool

def validate_bottle_spec(state: BottleState):
    if state['capacity'] > 0 and state['material'] in ['PET', 'Glass', 'HDPE']:
        return {'is_compliant': True}
    return {'is_compliant': False}

def route_by_compliance(state: BottleState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(BottleState)
graph.add_node('validate', validate_bottle_spec)
graph.add_node('process', lambda s: s)
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', route_by_compliance)
graph.set_entry_point('validate')
graph.set_finish_point('process')
graph.compile()
