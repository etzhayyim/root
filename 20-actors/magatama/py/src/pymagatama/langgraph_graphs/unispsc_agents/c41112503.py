from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlowmeterState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: FlowmeterState):
    required = ['range', 'fluid_type', 'pressure']
    validated = all(k in state['spec_data'] for k in required)
    return {'validated': validated}

def check_compliance(state: FlowmeterState):
    # Perform export control and material safety checks
    compliance = state['spec_data'].get('pressure', 0) < 500
    return {'compliance_check': compliance}

graph = StateGraph(FlowmeterState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
