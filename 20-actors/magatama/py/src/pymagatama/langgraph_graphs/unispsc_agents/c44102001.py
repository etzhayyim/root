from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaminationState(TypedDict):
    specs: dict
    validation_status: str

def validate_film_specs(state: LaminationState):
    required = ['thickness_microns', 'width_mm']
    if all(key in state['specs'] for key in required):
        val_status = 'verified'
    else:
        val_status = 'incomplete'
    return {'validation_status': val_status}

workflow = StateGraph(LaminationState)
workflow.add_node('verifier', validate_film_specs)
workflow.set_entry_point('verifier')
workflow.add_edge('verifier', END)
graph = workflow.compile()
