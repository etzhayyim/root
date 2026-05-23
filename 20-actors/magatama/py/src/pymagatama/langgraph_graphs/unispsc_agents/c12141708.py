from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PolymerState(TypedDict):
    material_id: str
    purity_level: float
    specs: dict
    is_compliant: bool

def validate_spec(state: PolymerState) -> PolymerState:
    state['is_compliant'] = state['purity_level'] > 99.5
    return state

def check_security(state: PolymerState) -> PolymerState:
    # Logic for dual-use export control validation
    if state['specs'].get('is_sensitive', False):
        print(f'Triggering security review for {state['material_id']}')
    return state

graph = StateGraph(PolymerState)
graph.add_node('validate', validate_spec)
graph.add_node('security', check_security)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
polymer_graph = graph.compile()
