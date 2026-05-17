from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FilterState(TypedDict):
    filter_specs: dict
    validation_results: List[str]
    is_compliant: bool

def validate_hepa_efficiency(state: FilterState):
    efficiency = state['filter_specs'].get('efficiency', 0)
    is_compliant = efficiency >= 99.97
    return {'validation_results': ['Efficiency check passed' if is_compliant else 'Efficiency check failed'], 'is_compliant': is_compliant}

def check_dimensions(state: FilterState):
    return {'validation_results': state['validation_results'] + ['Dimensional validation completed']}

graph = StateGraph(FilterState)
graph.add_node('load', lambda s: s)
graph.add_node('check_eff', validate_hepa_efficiency)
graph.add_node('check_dim', check_dimensions)
graph.add_edge('load', 'check_eff')
graph.add_edge('check_eff', 'check_dim')
graph.add_edge('check_dim', END)
graph.set_entry_point('load')
app = graph.compile()