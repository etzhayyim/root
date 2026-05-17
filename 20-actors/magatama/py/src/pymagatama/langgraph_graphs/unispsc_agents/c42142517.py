from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExtensionTubeState(TypedDict):
    spec_sheet: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_tube_specs(state: ExtensionTubeState):
    errors = []
    if 'luer_lock' not in state['spec_sheet']: errors.append('Missing Luer Lock')
    if 'sterilization' not in state['spec_sheet']: errors.append('Missing Sterilization Data')
    return {"is_compliant": len(errors) == 0, "validation_errors": errors}

graph = StateGraph(ExtensionTubeState)
graph.add_node("validate", validate_tube_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()