from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GeneratorPanelState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: GeneratorPanelState):
    errors = []
    if 'voltage' not in state['specifications']: errors.append('Missing voltage')
    if 'ip_rating' not in state['specifications']: errors.append('Missing IP rating')
    return {"validation_errors": errors, "approved": len(errors) == 0}

workflow = StateGraph(GeneratorPanelState)
workflow.add_node("validate", validate_specs)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()