from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: List[str]
    validation_status: bool

def validate_specs(state: ProcurementState):
    # Validation logic for place value model specifications
    is_valid = all(len(s) > 0 for s in state['specs'])
    return {'validation_status': is_valid}

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()