from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_materials(state: CastingState):
    material = state['spec_data'].get('material')
    valid = material in ['ABS', 'PolyCarbonate', 'Nylon', 'Epoxy']
    return {'validation_result': valid, 'error_log': [] if valid else ['Material type not supported']}

def check_dimensions(state: CastingState):
    tol = state['spec_data'].get('tolerance', 0.1)
    return {'validation_result': tol <= 0.05}

graph = StateGraph(CastingState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
app = graph.compile()
