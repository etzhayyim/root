from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_pressure(state: ValveState):
    pressure = state['specs'].get('pressure', 0)
    if pressure <= 0: return {'validation_passed': False, 'errors': ['Invalid pressure rating']}
    return {'validation_passed': True}

def check_compliance(state: ValveState):
    is_compliant = 'ISO' in state['specs'].get('certs', [])
    return {'validation_passed': is_compliant}

graph = StateGraph(ValveState)
graph.add_node('pressure_check', validate_pressure)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('pressure_check')
graph.add_edge('pressure_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()