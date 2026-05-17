from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorHomeState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: MotorHomeState):
    # Check for required safety and emission specs
    required = ['chassis_model', 'engine_emissions_rating']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_compliance(state: MotorHomeState):
    return 'compliant_node' if state['is_compliant'] else 'reject_node'

graph = StateGraph(MotorHomeState)
graph.add_node('validation', validate_specs)
graph.add_node('compliant_node', lambda s: s)
graph.add_node('reject_node', lambda s: s)
graph.set_entry_point('validation')
graph.add_conditional_edges('validation', check_compliance)
graph.add_edge('compliant_node', END)
graph.add_edge('reject_node', END)
graph.compile()