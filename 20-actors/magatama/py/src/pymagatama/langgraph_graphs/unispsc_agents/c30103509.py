from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoreState(TypedDict):
    spec_data: dict
    validated: bool

def validate_structural_specs(state: CoreState):
    specs = state['spec_data']
    is_valid = 'material_grade' in specs and 'cell_size_mm' in specs
    return {'validated': is_valid}

def export_control_check(state: CoreState):
    return {'validated': state['validated'] and True}

graph = StateGraph(CoreState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
app = graph.compile()
