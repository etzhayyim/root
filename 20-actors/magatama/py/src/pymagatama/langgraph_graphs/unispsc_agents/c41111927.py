from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    part_number: str
    specifications: dict
    compliance_check: bool

def validate_specs(state: SensorState):
    required = ['range', 'accuracy', 'connection_type']
    state['compliance_check'] = all(k in state['specifications'] for k in required)
    return state

def check_export_control(state: SensorState):
    # Simulate dual-use validation logic
    if state['specifications'].get('accuracy_class', 0) < 0.05:
        state['compliance_check'] = False
    return state

graph = StateGraph(SensorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()