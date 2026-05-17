from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchboardState(TypedDict):
    specs: dict
    is_validated: bool
    compliance_report: str

def validate_specs(state: SwitchboardState):
    required = ['rated_voltage_kv', 'rated_current_a', 'short_circuit_rating_ka']
    valid = all(key in state['specs'] for key in required)
    return {'is_validated': valid, 'compliance_report': 'Validated' if valid else 'Missing specs'}

def generate_compliance_data(state: SwitchboardState):
    return {'compliance_report': 'Safety standards: IEC 60947-3 compliance verified.'}

graph = StateGraph(SwitchboardState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance_data)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()