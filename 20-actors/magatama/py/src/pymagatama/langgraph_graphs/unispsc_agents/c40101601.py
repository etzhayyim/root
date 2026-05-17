from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlowerState(TypedDict):
    specs: dict
    validated: bool
    compliance_flag: bool

def validate_specs(state: BlowerState):
    required = ['motor_power_kw', 'pressure_rating_kpa']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid}

def check_compliance(state: BlowerState):
    is_dual = state['specs'].get('pressure_rating_kpa', 0) > 100
    return {'compliance_flag': is_dual}

graph = StateGraph(BlowerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()