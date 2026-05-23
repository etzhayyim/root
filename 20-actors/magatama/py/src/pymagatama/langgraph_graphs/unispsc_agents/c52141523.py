from typing import TypedDict
from langgraph.graph import StateGraph, END

class KettleState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: KettleState):
    required = ['voltage', 'safety_standard', 'material_food_grade']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

workflow = StateGraph(KettleState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
