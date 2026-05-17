from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    machine_id: str
    specifications: dict
    validation_status: bool

def validate_machinery_specs(state: PackagingState):
    check = state['specifications'].get('cycle_speed_ppm', 0) > 0
    return {'validation_status': check}

def route_by_validation(state: PackagingState):
    return 'valid' if state['validation_status'] else END

graph_builder = StateGraph(PackagingState)
graph_builder.add_node('validate', validate_machinery_specs)
graph_builder.set_entry_point('validate')
graph_builder.add_conditional_edges('validate', route_by_validation, {'valid': END})
graph = graph_builder.compile()