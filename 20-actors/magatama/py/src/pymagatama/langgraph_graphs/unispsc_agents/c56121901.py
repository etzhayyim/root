from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    table_specs: dict
    validation_results: list[str]

def validate_stability(state: ProcurementState):
    load = state['table_specs'].get('load_capacity', 0)
    if load < 50:
        state['validation_results'].append('Load capacity too low for industrial sewing machines.')
    return state

def check_dimensions(state: ProcurementState):
    if not state['table_specs'].get('dimensions'):
        state['validation_results'].append('Missing ergonomic dimension requirements.')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('stability_check', validate_stability)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('stability_check')
graph.add_edge('stability_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()
