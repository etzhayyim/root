from typing import TypedDict
from langgraph.graph import StateGraph, END

class FuelCellState(TypedDict):
    spec_data: dict
    is_validated: bool
    compliance_check: bool

def validate_specs(state: FuelCellState):
    required = ['power_output_kw', 'hydrogen_purity_requirement']
    valid = all(k in state['spec_data'] for k in required)
    return {'is_validated': valid}

def check_compliance(state: FuelCellState):
    return {'compliance_check': True}

graph = StateGraph(FuelCellState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()