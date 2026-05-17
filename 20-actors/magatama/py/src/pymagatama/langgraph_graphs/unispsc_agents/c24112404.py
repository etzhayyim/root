from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoxState(TypedDict):
    dimensions: dict
    material: str
    is_compliant: bool

def validate_specs(state: BoxState):
    # Basic validation logic for box dimensions and material compliance
    if state['dimensions']['depth'] > 0 and state['material']:
        return {'is_compliant': True}
    return {'is_compliant': False}

workflow = StateGraph(BoxState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()