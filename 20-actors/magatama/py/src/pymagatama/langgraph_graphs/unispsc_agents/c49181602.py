from langgraph.graph import StateGraph, END
from typing import TypedDict

class ArcheryState(TypedDict):
    specs: dict
    is_compliant: bool
    export_cleared: bool

def validate_specs(state: ArcheryState):
    weight = state['specs'].get('draw_weight_lbs', 0)
    return {'is_compliant': weight > 0}

def check_export_controls(state: ArcheryState):
    return {'export_cleared': True}

graph = StateGraph(ArcheryState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
