from typing import TypedDict
from langgraph.graph import StateGraph, END

class TasselState(TypedDict):
    spec_data: dict
    approved: bool
    validation_log: list

def validate_specs(state: TasselState):
    """Validates technical specifications for textile tassels."""
    reqs = ['Material', 'Colorfastness', 'Flammability']
    logs = []
    is_valid = all(key in state['spec_data'] for key in reqs)
    if not is_valid:
        logs.append("Missing required specifications.")
    return {"approved": is_valid, "validation_log": logs}

workflow = StateGraph(TasselState)
workflow.add_node("validate", validate_specs)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()