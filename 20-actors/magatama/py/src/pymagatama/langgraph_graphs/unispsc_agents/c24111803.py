from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TankState(TypedDict):
    capacity: float
    material: str
    is_pressure_vessel: bool
    compliance_docs: List[str]
    approved: bool

def validate_specs(state: TankState):
    if state['material'] == 'stainless' and state.get('capacity', 0) > 0:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(TankState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()