from typing import TypedDict
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    item_name: str
    purity_verified: bool
    appraisal_attached: bool
    is_compliant: bool

def check_purity(state: JewelryState):
    state['purity_verified'] = True
    return state

def verify_appraisal(state: JewelryState):
    state['is_compliant'] = state['purity_verified'] and state['appraisal_attached']
    return state

graph = StateGraph(JewelryState)
graph.add_node('check_purity', check_purity)
graph.add_node('verify_appraisal', verify_appraisal)
graph.add_edge('check_purity', 'verify_appraisal')
graph.add_edge('verify_appraisal', END)
graph.set_entry_point('check_purity')
graph = graph.compile()
