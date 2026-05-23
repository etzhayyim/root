from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShavingCreamState(TypedDict):
    chemical_data: dict
    is_compliant: bool
    compliance_report: str

def validate_chemistry(state: ShavingCreamState):
    # Business logic for ingredient safety screening
    restricted = ['parabens', 'formaldehyde']
    ingredients = state['chemical_data'].get('ingredients', [])
    compliant = not any(item in restricted for item in ingredients)
    return {'is_compliant': compliant, 'compliance_report': 'Safety check performed.'}

def finalize_procurement(state: ShavingCreamState):
    return {'compliance_report': 'Procurement criteria met.' if state['is_compliant'] else 'Rejected due to hazard.'}

graph = StateGraph(ShavingCreamState)
graph.add_node('validate', validate_chemistry)
graph.add_node('final', finalize_procurement)
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph.set_entry_point('validate')
graph = graph.compile()
