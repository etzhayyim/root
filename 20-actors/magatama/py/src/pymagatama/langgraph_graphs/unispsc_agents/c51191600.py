from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectrolyteState(TypedDict):
    purity_level: float
    safety_compliance: bool
    approved: bool

def validate_purity(state: ElectrolyteState):
    state['approved'] = state['purity_level'] >= 99.9
    return state

def check_regulations(state: ElectrolyteState):
    if not state['safety_compliance']:
        state['approved'] = False
    return state

graph = StateGraph(ElectrolyteState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_regulations', check_regulations)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_regulations')
graph.add_edge('check_regulations', END)
graph = graph.compile()