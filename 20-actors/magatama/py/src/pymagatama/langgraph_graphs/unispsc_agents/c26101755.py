from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveGuideState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: ValveGuideState):
    required = ['material_grade', 'od_tolerance', 'id_tolerance']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

workflow = StateGraph(ValveGuideState)
workflow.add_node('validator', validate_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()
