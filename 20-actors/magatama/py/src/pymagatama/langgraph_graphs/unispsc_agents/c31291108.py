from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MagnesiumSpecState(TypedDict):
    part_number: str
    material_grade: str
    tolerance: float
    is_verified: bool
    validation_log: List[str]

def validate_material(state: MagnesiumSpecState):
    grade = state['material_grade']
    valid = grade.startswith('AZ') or grade.startswith('ZK')
    return {'is_verified': valid, 'validation_log': [f'Material grade {grade} status: {valid}']}

def check_tolerances(state: MagnesiumSpecState):
    tol = state['tolerance']
    success = tol <= 0.05
    return {'validation_log': state['validation_log'] + [f'Tolerance check (<= 0.05mm): {success}']}

graph = StateGraph(MagnesiumSpecState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_tolerances', check_tolerances)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_tolerances')
graph.add_edge('check_tolerances', END)
graph = graph.compile()