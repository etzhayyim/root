from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class FastenerState(TypedDict):
    part_number: str
    material: str
    tensile_data: float
    validation_log: Annotated[list[str], operator.add]

def validate_material(state: FastenerState):
    log = ['Material check passed' if state['material'] in ['Steel', 'Aluminum'] else 'Material invalid']
    return {'validation_log': log}

def validate_tensile(state: FastenerState):
    log = ['Tensile strength exceeds threshold' if state['tensile_data'] > 500 else 'Tensile strength insufficient']
    return {'validation_log': log}

graph = StateGraph(FastenerState)
graph.add_node('material_check', validate_material)
graph.add_node('tensile_check', validate_tensile)
graph.add_edge('material_check', 'tensile_check')
graph.add_edge('tensile_check', END)
graph.set_entry_point('material_check')

compile = graph.compile()