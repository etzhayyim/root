from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    composition: Dict[str, float]
    compliance_checks: List[str]
    status: str

def validate_composition(state: MineralState) -> MineralState:
    if state['composition'].get('purity', 0) < 95.0:
        state['status'] = 'REJECTED'
    else:
        state['status'] = 'COMPLIANCE_REVIEW'
    return state

def check_sanctions(state: MineralState) -> MineralState:
    if state['status'] == 'COMPLIANCE_REVIEW':
        state['compliance_checks'].append('sanctions_cleared')
        state['status'] = 'APPROVED'
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_composition)
graph.add_node('sanctions', check_sanctions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sanctions')
graph.add_edge('sanctions', END)

# Compilation
app = graph.compile()
