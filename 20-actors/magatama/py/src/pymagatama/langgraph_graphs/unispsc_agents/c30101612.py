from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZincProcurementState(TypedDict):
    purity_level: float
    weight_kg: float
    compliance_checked: bool

def validate_purity(state: ZincProcurementState):
    state['compliance_checked'] = state['purity_level'] >= 99.9
    return state

def check_weight_limit(state: ZincProcurementState):
    return {'compliance_checked': state['weight_kg'] < 5000}

graph = StateGraph(ZincProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_weight_limit', check_weight_limit)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_weight_limit')
graph.add_edge('check_weight_limit', END)
app = graph.compile()
