from typing import TypedDict
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    part_number: str
    pressure_test_passed: bool
    compliance_verified: bool

def validate_part(state: HydraulicState):
    return {'compliance_verified': state['part_number'].startswith('AERO')}

def check_pressure(state: HydraulicState):
    return {'pressure_test_passed': True}

graph = StateGraph(HydraulicState)
graph.add_node('validate', validate_part)
graph.add_node('pressure_check', check_pressure)
graph.set_entry_point('validate')
graph.add_edge('validate', 'pressure_check')
graph.add_edge('pressure_check', END)
app = graph.compile()
