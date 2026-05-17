from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    part_id: str
    specs: dict
    is_compliant: bool

def validate_specs(state: RobotState):
    # Simulate CAD and physical constraint validation
    compliant = state['specs'].get('load_capacity', 0) > 0
    return {'is_compliant': compliant}

def finalize_order(state: RobotState):
    return {'status': 'READY_FOR_Procurement'}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('order', finalize_order)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
graph = graph.compile()