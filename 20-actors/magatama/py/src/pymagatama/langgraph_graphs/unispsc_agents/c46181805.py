from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FilterState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: FilterState):
    errors = []
    if 'screen_size_inch' not in state['specs']: errors.append('Missing screen size')
    if 'filter_type' not in state['specs']: errors.append('Missing filter type')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(FilterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()