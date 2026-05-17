from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    specs: dict
    validation_log: Annotated[list, operator.add]
    is_compliant: bool

def validate_pressure_rating(state: ValveState):
    pressure = state['specs'].get('pressure', 0)
    is_valid = pressure > 0
    return {'validation_log': [f'Pressure check: {pressure} bar'], 'is_compliant': is_valid}

def check_material_safety(state: ValveState):
    material = state['specs'].get('body_material', 'unknown')
    is_safe = material in ['SUS304', 'SUS316', 'Cast Iron']
    return {'validation_log': [f'Material check: {material}'], 'is_compliant': is_safe}

graph = StateGraph(ValveState)
graph.add_node('pressure_check', validate_pressure_rating)
graph.add_node('material_check', check_material_safety)
graph.set_entry_point('pressure_check')
graph.add_edge('pressure_check', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()