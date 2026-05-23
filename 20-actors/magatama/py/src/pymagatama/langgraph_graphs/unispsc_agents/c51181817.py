from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    api_purity: float
    storage_temp: str
    gmp_verified: bool

def validate_purity(state: PharmState):
    assert state['api_purity'] >= 99.0, 'Purity below standard'
    return {'status': 'Purity Validated'}

def verify_gmp(state: PharmState):
    return {'status': 'GMP Certified' if state['gmp_verified'] else 'Rejected'}

graph = StateGraph(PharmState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_gmp', verify_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_gmp')
graph.add_edge('verify_gmp', END)
graph = graph.compile()
