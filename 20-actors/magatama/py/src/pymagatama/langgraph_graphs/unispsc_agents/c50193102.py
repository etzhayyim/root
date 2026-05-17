from typing import TypedDict
from langgraph.graph import StateGraph, END

class DessertMixState(TypedDict):
    product_specs: dict
    compliance_ok: bool
    qc_passed: bool

def validate_allergens(state: DessertMixState) -> DessertMixState:
    allergens = state['product_specs'].get('allergens', [])
    state['compliance_ok'] = 'major_allergen' not in allergens
    return state

def run_qc_inspection(state: DessertMixState) -> DessertMixState:
    state['qc_passed'] = state['compliance_ok'] and state['product_specs'].get('temp_control')
    return state

graph = StateGraph(DessertMixState)
graph.add_node('validate', validate_allergens)
graph.add_node('qc', run_qc_inspection)
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph.set_entry_point('validate')
graph = graph.compile()