from langgraph.graph import StateGraph, END
from typing import TypedDict

class RefractoryState(TypedDict):
    material_type: str
    thermal_rating: float
    compliance_docs: bool

def validate_specs(state: RefractoryState):
    print(f'Validating thermal resistance: {state['thermal_rating']}')
    return {'compliance_docs': state['thermal_rating'] > 1500}

workflow = StateGraph(RefractoryState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()