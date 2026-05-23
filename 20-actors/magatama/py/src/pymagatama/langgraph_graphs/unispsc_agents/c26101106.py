from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: str

def validate_specs(state: MotorState):
    required = ['rated_power_kw', 'voltage_rating', 'efficiency_class_ie']
    is_valid = all(k in state['specs'] for k in required)
    return {'validated': is_valid}

def check_compliance(state: MotorState):
    # Dual-use export control logic placeholder
    if state['specs'].get('rated_power_kw', 0) > 500:
         return {'compliance_check': 'REQUIRED_EXPORT_LICENSE'}
    return {'compliance_check': 'PASSED'}

graph = StateGraph(MotorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
