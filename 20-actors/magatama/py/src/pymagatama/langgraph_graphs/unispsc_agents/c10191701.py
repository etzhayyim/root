from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity: float
    origin: str
    compliance_checks: Annotated[Sequence[str], operator.add]
    status: str

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] < 0.98:
        return {'status': 'REJECTED_LOW_PURITY'}
    return {'status': 'PURITY_VALIDATED'}

def check_sanctions(state: MineralState) -> MineralState:
    if state['origin'] in ['restricted_zone_a', 'restricted_zone_b']:
        return {'compliance_checks': ['SANCTION_FAILED'], 'status': 'BLOCKED'}
    return {'compliance_checks': ['SANCTION_CLEARED'], 'status': 'COMPLIANCE_CLEARED'}

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sanctions', check_sanctions)
graph.add_edge('validate_purity', 'check_sanctions')
graph.add_edge('check_sanctions', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()