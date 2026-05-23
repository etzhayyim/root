from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    origin: str
    compliance_cleared: bool

def validate_origin(state: MineralState) -> MineralState:
    # Logic to verify origin against sanctions list
    state['compliance_cleared'] = state['origin'] not in ['restricted_region_a', 'restricted_region_b']
    return state

def check_purity(state: MineralState) -> MineralState:
    # Logic to validate industrial grade thresholds
    if state['purity'] < 0.95:
        print(f'Purity {state['purity']} below industrial standard.')
    return state

workflow = StateGraph(MineralState)
workflow.add_node('validate_origin', validate_origin)
workflow.add_node('check_purity', check_purity)
workflow.set_entry_point('validate_origin')
workflow.add_edge('validate_origin', 'check_purity')
workflow.add_edge('check_purity', END)

graph = workflow.compile()
