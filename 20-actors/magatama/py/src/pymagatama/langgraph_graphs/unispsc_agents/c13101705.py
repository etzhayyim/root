from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    material_id: str
    purity_level: float
    status: str
    log: List[str]

def validate_quality(state: MineralProcurementState) -> MineralProcurementState:
    if state.get('purity_level', 0) < 99.9:
        state['status'] = 'REJECTED'
        state['log'].append('Quality check failed: Insufficient purity')
    else:
        state['status'] = 'VALIDATED'
    return state

def route_procurement(state: MineralProcurementState) -> str:
    return 'END' if state['status'] == 'VALIDATED' else 'END'

graph = StateGraph(MineralProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()
