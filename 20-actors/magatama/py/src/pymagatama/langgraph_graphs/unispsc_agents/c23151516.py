from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: WeldingState):
    specs = state['spec_data']
    valid = specs.get('output_power_kw', 0) > 0 and 'safety_certification_standard' in specs
    return {'is_compliant': valid, 'validation_log': ['Safety and power criteria checked']}

def route_by_compliance(state: WeldingState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(WeldingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'non_compliant': END})
graph.compile()