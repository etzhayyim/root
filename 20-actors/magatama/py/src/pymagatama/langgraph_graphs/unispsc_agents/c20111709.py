from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    status: str

def validate_pressure_rating(state: ActuatorState) -> ActuatorState:
    pressure = state['spec_data'].get('maximum_operating_pressure_mpa', 0)
    if pressure > 35.0:
        return {'validation_results': ['High pressure rating requires safety audit']}
    return {'validation_results': ['Pressure rating within standard limits']}

def check_material_specs(state: ActuatorState) -> ActuatorState:
    material = state['spec_data'].get('material_specification', 'unknown')
    if material == 'high-grade-steel':
        return {'validation_results': ['Material compliant with heavy-duty ops']}
    return {'validation_results': ['Material needs secondary approval']}

def build_actuator_graph():
    graph = StateGraph(ActuatorState)
    graph.add_node('validate_pressure', validate_pressure_rating)
    graph.add_node('check_material', check_material_specs)
    graph.set_entry_point('validate_pressure')
    graph.add_edge('validate_pressure', 'check_material')
    graph.add_edge('check_material', END)
    return graph.compile()

graph = build_actuator_graph()