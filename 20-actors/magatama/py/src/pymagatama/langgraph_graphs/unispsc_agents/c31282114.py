from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    component_name: str
    purity_level: float
    specs: List[str]
    is_validated: bool

def validate_precious_metal(state: ProcurementState):
    if state['purity_level'] >= 0.99:
        return {'is_validated': True}
    return {'is_validated': False}

def security_check(state: ProcurementState):
    print('Running dual-use export control audit...')
    return {}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_precious_metal)
graph.add_node('security', security_check)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()
