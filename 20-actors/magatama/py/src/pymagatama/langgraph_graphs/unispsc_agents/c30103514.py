from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoreState(TypedDict):
    material_spec: dict
    validation_status: bool
    export_control_check: bool

def validate_specs(state: CoreState):
    # Business logic for aerospace honeycomb validation
    is_valid = all(key in state['material_spec'] for key in ['grade', 'density'])
    return {'validation_status': is_valid}

def check_dual_use(state: CoreState):
    # Regulatory logic for export control classification
    return {'export_control_check': True}

graph = StateGraph(CoreState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()
