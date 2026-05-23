from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_number: str
    specifications: dict
    validation_status: bool

def validate_terminal_specs(state: ProcurementState):
    specs = state.get('specifications', {})
    required = ['wire_gauge', 'voltage_rating']
    is_valid = all(key in specs for key in required)
    return {'validation_status': is_valid}

def route_by_validation(state: ProcurementState):
    return 'valid' if state['validation_status'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validator', validate_terminal_specs)
graph.set_entry_point('validator')
graph.add_conditional_edges('validator', route_by_validation, {'valid': 'assembly_workflow', 'end': END})
graph.add_node('assembly_workflow', lambda x: x)
graph.add_edge('assembly_workflow', END)
graph = graph.compile()
