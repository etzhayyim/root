from typing import TypedDict
from langgraph.graph import StateGraph, END

class HexNutState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_material(state: HexNutState):
    grade = state['spec_data'].get('material_grade')
    is_valid = grade in ['Grade 5', 'Grade 8', 'A4-70', 'Class 8.8']
    return {'validation_passed': is_valid}

def validate_dimensions(state: HexNutState):
    tolerance = state['spec_data'].get('tolerance')
    is_valid = tolerance <= 0.05
    return {'validation_passed': state['validation_passed'] and is_valid}

graph = StateGraph(HexNutState)
graph.add_node('validate_material', validate_material)
graph.add_node('validate_dimensions', validate_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'validate_dimensions')
graph.add_edge('validate_dimensions', END)
graph = graph.compile()