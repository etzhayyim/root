from typing import TypedDict
from langgraph.graph import StateGraph, END

class VehicleTrimState(TypedDict):
    part_number: str
    material_spec: str
    validation_passed: bool

def validate_trim_specs(state: VehicleTrimState):
    # Simulate CAD and material compliance check
    is_compliant = 'UV_RESISTANT' in state['material_spec']
    return {'validation_passed': is_compliant}

def route_by_validation(state: VehicleTrimState):
    return 'process' if state['validation_passed'] else END

graph_builder = StateGraph(VehicleTrimState)
graph_builder.add_node('validate', validate_trim_specs)
graph_builder.add_edge('validate', END)
graph_builder.set_entry_point('validate')
graph = graph_builder.compile()