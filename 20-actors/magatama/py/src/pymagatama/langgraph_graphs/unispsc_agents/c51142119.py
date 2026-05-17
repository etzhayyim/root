from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BenorilateState(TypedDict):
    batch_id: str
    purity_level: float
    has_coa: bool
    approved: bool

def validate_purity(state: BenorilateState):
    is_valid = state['purity_level'] >= 99.5 and state['has_coa']
    print(f'Validating batch {state['batch_id']}: {is_valid}')
    return {'approved': is_valid}

workflow = StateGraph(BenorilateState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()