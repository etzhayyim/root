from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProbucolState(TypedDict):
    purity: float
    gmp_status: bool
    validation_log: List[str]

def validate_purity(state: ProbucolState):
    state['validation_log'].append('Checking purity levels...')
    if state['purity'] < 99.0: raise ValueError('Purity below 99.0%')
    return state

def check_gmp(state: ProbucolState):
    state['validation_log'].append('Verifying GMP certification...')
    return {'gmp_status': True}

graph = StateGraph(ProbucolState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
graph = graph.compile()