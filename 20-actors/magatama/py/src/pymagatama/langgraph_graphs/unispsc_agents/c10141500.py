from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    commodity_id: str
    viscosity: float
    purity: float
    status: str

def validate_quality(state: ChemicalState):
    if state['purity'] >= 0.98:
        return {'status': 'quality_approved'}
    return {'status': 'quality_failed'}

def check_hazard(state: ChemicalState):
    # Simulate DG regulation check
    return {'status': 'hazard_check_passed'}

def build_graph():
    graph = StateGraph(ChemicalState)
    graph.add_node('validate', validate_quality)
    graph.add_node('hazard', check_hazard)
    graph.add_edge('validate', 'hazard')
    graph.add_edge('hazard', END)
    graph.set_entry_point('validate')
    return graph.compile()

graph = build_graph()