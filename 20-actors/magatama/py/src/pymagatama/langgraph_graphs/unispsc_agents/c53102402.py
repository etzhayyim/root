from typing import TypedDict
from langgraph.graph import StateGraph, END

class SockState(TypedDict):
    material_data: dict
    compliance_score: float

def validate_materials(state: SockState):
    # Custom logic to check material composition ratios for socks
    composition = state['material_data'].get('composition', {})
    score = 1.0 if sum(composition.values()) == 100 else 0.0
    return {'compliance_score': score}

workflow = StateGraph(SockState)
workflow.add_node('validate', validate_materials)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
