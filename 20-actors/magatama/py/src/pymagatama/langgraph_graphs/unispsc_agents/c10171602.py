from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralFertilizerState(TypedDict):
    commodity_code: str
    batch_id: str
    purity_level: float
    inspection_passed: bool

def validate_purity(state: MineralFertilizerState):
    # Business logic: reject batches below 95% purity
    if state['purity_level'] < 0.95:
        return {'inspection_passed': False}
    return {'inspection_passed': True}

def route_supply(state: MineralFertilizerState):
    if state['inspection_passed']:
        return 'approve'
    return 'quarantine'

workflow = StateGraph(MineralFertilizerState)
workflow.add_node('validate', validate_purity)
workflow.add_edge('validate', route_supply)
workflow.add_edge('approve', END)
workflow.add_edge('quarantine', END)
workflow.set_entry_point('validate')
graph = workflow.compile()