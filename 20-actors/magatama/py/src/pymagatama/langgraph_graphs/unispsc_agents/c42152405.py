from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalMaterialState(TypedDict):
    material_id: str
    compliance_docs: list
    is_approved: bool

def validate_biocompatibility(state: DentalMaterialState):
    state['is_approved'] = 'ISO_10993' in state['compliance_docs']
    return state

def check_regulatory_status(state: DentalMaterialState):
    print(f'Checking {state["material_id"]} regulatory criteria...')
    return state

graph = StateGraph(DentalMaterialState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('regulatory', check_regulatory_status)
graph.add_edge('regulatory', 'validate')
graph.add_edge('validate', END)
graph.set_entry_point('regulatory')
graph = graph.compile()
