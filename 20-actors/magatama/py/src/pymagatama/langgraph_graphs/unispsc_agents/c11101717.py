from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity_level: float
    safety_clearance: bool
    logistics_status: str
    validation_history: List[str]

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity_level'] >= 0.99:
        state['validation_history'].append('Purity validated at high grade.')
        state['safety_clearance'] = True
    else:
        state['safety_clearance'] = False
    return state

def route_logistics(state: ChemicalState) -> str:
    return 'VALID' if state['safety_clearance'] else 'FAIL'

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', 'route_logistics')
graph.add_conditional_edges('route_logistics', lambda s: 'VALID' if s['safety_clearance'] else 'FAIL', {'VALID': END, 'FAIL': END})
graph.set_entry_point('validate')
compiled_graph = graph.compile()