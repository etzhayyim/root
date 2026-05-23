from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ForgingState(TypedDict):
    spec_data: dict
    validation_checks: List[str]
    approved: bool

def validate_materials(state: ForgingState):
    grade = state['spec_data'].get('grade')
    is_valid = grade in ['ASTM A576', 'AISI 1045']
    return {'validation_checks': ['Material Grade Verified'] if is_valid else ['Material Grade Invalid']}

def check_dimensions(state: ForgingState):
    tolerance = state['spec_data'].get('tolerance', 0.0)
    status = 'Dimensional Check Passed' if tolerance <= 0.05 else 'Manual Review Required'
    return {'validation_checks': state['validation_checks'] + [status]}

graph = StateGraph(ForgingState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
