from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SeedState(TypedDict):
    batch_id: str
    germination_rate: float
    has_phytosanitary_cert: bool
    is_approved: bool

def validate_quality(state: SeedState) -> SeedState:
    if state['germination_rate'] >= 0.85 and state['has_phytosanitary_cert']:
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

def process_shipment(state: SeedState) -> SeedState:
    print(f'Processing seed batch {state['batch_id']}. Approval: {state['is_approved']}')
    return state

workflow = StateGraph(SeedState)
workflow.add_node('validate', validate_quality)
workflow.add_node('ship', process_shipment)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'ship')
workflow.add_edge('ship', END)
graph = workflow.compile()
