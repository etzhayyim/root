from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    sds_verified: bool
    hazard_class: str

def validate_purity(state: ChemicalState):
    if state['purity'] < 0.98:
        raise ValueError('Purity below 98% threshold')
    return {'status': 'validated'}

def check_sds(state: ChemicalState):
    return {'sds_verified': True}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('sds_check', check_sds)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sds_check')
graph.add_edge('sds_check', END)
graph = graph.compile()
