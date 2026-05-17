from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_emissions(state: TractorState):
    emission_val = state['spec_data'].get('Engine_Emission_Rating')
    is_valid = emission_val in ['Tier4', 'StageV']
    return {'validation_results': [f'Emissions compliant: {is_valid}'], 'is_compliant': is_valid}

def check_safety(state: TractorState):
    has_rops = state['spec_data'].get('ROPS_Certification_Standard') is not None
    return {'validation_results': state['validation_results'] + [f'ROPS certified: {has_rops}']}

graph = StateGraph(TractorState)
graph.add_node('validate_emissions', validate_emissions)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate_emissions')
graph.add_edge('validate_emissions', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()