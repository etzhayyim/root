from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbsorbentState(TypedDict):
    absorbency_rate: float
    chemical_type: str
    is_compliant: bool

def validate_absorbent(state: AbsorbentState):
    state['is_compliant'] = state['absorbency_rate'] > 5.0 and state['chemical_type'] != 'corrosive'
    return state

def check_sds(state: AbsorbentState):
    print('Verifying SDS documents for regulatory compliance...')
    return state

graph = StateGraph(AbsorbentState)
graph.add_node('validate', validate_absorbent)
graph.add_node('sds_check', check_sds)
graph.add_edge('validate', 'sds_check')
graph.add_edge('sds_check', END)
graph.set_entry_point('validate')
graph = graph.compile()