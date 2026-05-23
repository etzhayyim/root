from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChainState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: ChainState):
    specs = state['spec_data']
    errors = []
    if 'pitch_size' not in specs: errors.append('Pitch size missing')
    if 'tensile_strength' not in specs: errors.append('Tensile strength required')
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: ChainState):
    return 'process' if state['validated'] else END

graph = StateGraph(ChainState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'error_log': ['Order sent to fabrication']})

graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph = graph.compile()
