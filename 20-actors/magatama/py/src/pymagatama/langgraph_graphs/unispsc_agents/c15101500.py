from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class HoseState(TypedDict):
    spec: dict
    validation_results: List[str]

def validate_pressure(state: HoseState):
    pressure = state['spec'].get('burst_pressure_rating_mpa', 0)
    if pressure < 1.0:
        return {'validation_results': ['Pressure too low for industrial grade']}
    return {'validation_results': ['Pressure check passed']}

def validate_material(state: HoseState):
    material = state['spec'].get('material_composition_compliance')
    if not material:
        return {'validation_results': ['Missing compliance info']}
    return {'validation_results': ['Material compliance confirmed']}

graph = StateGraph(HoseState)
graph.add_node('pressure_check', validate_pressure)
graph.add_node('material_check', validate_material)
graph.add_edge('pressure_check', 'material_check')
graph.add_edge('material_check', END)
graph.set_entry_point('pressure_check')
compiled_graph = graph.compile()