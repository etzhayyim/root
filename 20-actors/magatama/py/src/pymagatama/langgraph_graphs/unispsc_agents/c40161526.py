from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterSpecState(TypedDict):
    material_spec: str
    pressure_test_result: float
    is_compliant: bool

def validate_material(state: FilterSpecState):
    state['is_compliant'] = state['material_spec'] == 'Stainless Steel 316'
    return state

def check_pressure(state: FilterSpecState):
    if state['pressure_test_result'] < 10.0:
        state['is_compliant'] = False
    return state

graph_builder = StateGraph(FilterSpecState)
graph_builder.add_node('validate_material', validate_material)
graph_builder.add_node('check_pressure', check_pressure)
graph_builder.set_entry_point('validate_material')
graph_builder.add_edge('validate_material', 'check_pressure')
graph_builder.add_edge('check_pressure', END)
graph = graph_builder.compile()
