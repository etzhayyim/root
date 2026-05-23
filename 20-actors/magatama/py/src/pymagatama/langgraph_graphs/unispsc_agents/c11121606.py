from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    material_id: str
    purity: float
    compliance_passed: bool
    log: List[str]

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] >= 99.9:
        state['compliance_passed'] = True
        state['log'].append('Purity check passed')
    else:
        state['compliance_passed'] = False
        state['log'].append('Purity below 99.9% threshold')
    return state

def check_sanctions(state: MineralState) -> MineralState:
    state['log'].append('Sanction screening complete')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sanctions', check_sanctions)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_sanctions')
graph.add_edge('check_sanctions', END)

compiled_graph = graph.compile()
