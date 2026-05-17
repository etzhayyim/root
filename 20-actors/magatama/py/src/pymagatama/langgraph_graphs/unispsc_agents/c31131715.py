from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    material_data: dict
    compliance_report: str
    approved: bool

def validate_lead_specs(state: ForgingState):
    purity = state['material_data'].get('purity', 0)
    state['approved'] = purity >= 99.9
    state['compliance_report'] = 'Accepted' if state['approved'] else 'Rejected due to low purity'
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_lead_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()