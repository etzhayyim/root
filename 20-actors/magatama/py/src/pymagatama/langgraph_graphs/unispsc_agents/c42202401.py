from typing import TypedDict
from langgraph.graph import StateGraph, END

class PETUnitState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_shielding(state: PETUnitState):
    shielding = state['spec_data'].get('shielding_mm', 0)
    valid = shielding >= 10
    return {'validation_results': [f'Shielding at {shielding}mm: {valid}'], 'is_compliant': valid}

def check_regulations(state: PETUnitState):
    compliance = state['spec_data'].get('iec_60601_certified', False)
    return {'is_compliant': state['is_compliant'] and compliance}

graph = StateGraph(PETUnitState)
graph.add_node('shielding_check', validate_shielding)
graph.add_node('regulatory_check', check_regulations)
graph.set_entry_point('shielding_check')
graph.add_edge('shielding_check', 'regulatory_check')
graph.add_edge('regulatory_check', END)
graph = graph.compile()
