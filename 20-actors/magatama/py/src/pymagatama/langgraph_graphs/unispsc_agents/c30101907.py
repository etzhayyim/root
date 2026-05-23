from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    purity: float
    mass: float
    certification_docs: List[str]
    validated: bool

def validate_purity(state: MagnesiumState):
    state['validated'] = state['purity'] >= 99.9
    return state

def check_hazard(state: MagnesiumState):
    print('Checking dangerous goods status for flammable metal')
    return state

graph = StateGraph(MagnesiumState)
graph.add_node('validate', validate_purity)
graph.add_node('hazard_check', check_hazard)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazard_check')
graph.add_edge('hazard_check', END)
graph = graph.compile()
