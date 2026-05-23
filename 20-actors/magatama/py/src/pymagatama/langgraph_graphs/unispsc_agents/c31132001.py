from typing import TypedDict
from langgraph.graph import StateGraph, END

class SinteredComponentState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_density(state: SinteredComponentState):
    density = state['specs'].get('density', 0)
    state['validation_passed'] = density >= 6.8
    return 'checked'

def check_dimensions(state: SinteredComponentState):
    state['validation_passed'] = state['validation_passed'] and state['specs'].get('tolerance_check', False)
    return 'checked'

graph = StateGraph(SinteredComponentState)
graph.add_node('density_check', validate_density)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('density_check')
graph.add_edge('density_check', 'dimension_check')
graph.add_edge('dimension_check', END)
app = graph.compile()
