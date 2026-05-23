from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity: float
    safety_clearance: bool
    logistics_status: str

def validate_purity(state: ChemicalState):
    state['safety_clearance'] = state['purity'] >= 99.9
    return state

def route_logistics(state: ChemicalState):
    if state['safety_clearance']:
        state['logistics_status'] = 'READY_FOR_HAZMAT_TRANSPORT'
    else:
        state['logistics_status'] = 'HOLD_QUALITY_REVIEW'
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('route', route_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'route')
graph.add_edge('route', END)
app = graph.compile()
