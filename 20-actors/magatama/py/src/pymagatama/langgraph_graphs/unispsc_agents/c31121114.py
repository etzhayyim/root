from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    material_data: dict
    validation_results: list
    is_compliant: bool

def validate_lead_cast(state: CastState):
    purity = state['material_data'].get('purity_level', 99.9)
    compliant = purity >= 99.0
    return {'is_compliant': compliant, 'validation_results': ['Purity check passed' if compliant else 'Purity failed']}

workflow = StateGraph(CastState)
workflow.add_node('validate', validate_lead_cast)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()