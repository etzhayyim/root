from langgraph.graph import StateGraph, END
from typing import TypedDict

class KitState(TypedDict):
    kit_id: str
    compliance_passed: bool
    needs_calibration: bool

def validate_certification(state: KitState):
    print(f'Validating cert for kit: {state[\'kit_id\']}')
    return {'compliance_passed': True}

def check_maintenance(state: KitState):
    print('Checking expiration and maintenance schedule')
    return {'needs_calibration': False}

graph = StateGraph(KitState)
graph.add_node('validate', validate_certification)
graph.add_node('maintenance', check_maintenance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'maintenance')
graph.add_edge('maintenance', END)
graph = graph.compile()