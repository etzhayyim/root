from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GasSupplyState(TypedDict):
    commodity_code: str
    pressure: float
    purity_level: float
    compliance_checks: List[str]
    status: str

def validate_pressure(state: GasSupplyState):
    is_valid = state['pressure'] > 500
    return {'status': 'pressure_ok' if is_valid else 'pressure_fail'}

def check_purity(state: GasSupplyState):
    purity_ok = state['purity_level'] >= 98.5
    return {'compliance_checks': ['purity_standard'] if purity_ok else []}

graph = StateGraph(GasSupplyState)
graph.add_node('validate_pressure', validate_pressure)
graph.add_node('check_purity', check_purity)
graph.add_edge('validate_pressure', 'check_purity')
graph.add_edge('check_purity', END)
graph.set_entry_point('validate_pressure')
graph = graph.compile()