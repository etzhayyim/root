from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_checks: Annotated[List[str], operator.add]
    is_cleared: bool

def validate_purity(state: MineralState):
    cleared = state['purity_level'] >= 95.0
    return {'compliance_checks': ['purity_verified'], 'is_cleared': cleared}

def check_origin(state: MineralState):
    return {'compliance_checks': ['origin_verified']}

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_origin', check_origin)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_origin')
graph.add_edge('check_origin', END)

graph = graph.compile()