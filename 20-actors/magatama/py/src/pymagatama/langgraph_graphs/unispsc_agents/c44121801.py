from langgraph.graph import StateGraph, END
from typing import TypedDict

class CorrectionSupplyState(TypedDict):
    product_name: str
    tape_specs: dict
    approved: bool

def validate_tape(state: CorrectionSupplyState):
    width = state['tape_specs'].get('width', 0)
    state['approved'] = 4.0 <= width <= 12.0
    return state

workflow = StateGraph(CorrectionSupplyState)
workflow.add_node('validate', validate_tape)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
