from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CentrifugeState(TypedDict):
    specs: dict
    validation_status: bool
    compliance_check: bool

def validate_specs(state: CentrifugeState):
    required = ['Max_RPM', 'Rotor_Type']
    valid = all(k in state['specs'] for k in required)
    return {'validation_status': valid}

def check_compliance(state: CentrifugeState):
    is_compliant = state.get('validation_status', False) and state['specs'].get('Safety_Cert')
    return {'compliance_check': is_compliant}

graph = StateGraph(CentrifugeState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
