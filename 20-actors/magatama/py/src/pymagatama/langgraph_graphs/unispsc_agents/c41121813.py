from typing import TypedDict
from langgraph.graph import StateGraph, END

class CuvetteState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: CuvetteState):
    specs = state['spec_data']
    is_valid = all(k in specs for k in ['optical_path_length_mm', 'material_type'])
    print(f'Validating cuvette specs: {is_valid}')
    return {'validated': is_valid}

def route_by_validation(state: CuvetteState):
    return 'process' if state['validated'] else END

graph = StateGraph(CuvetteState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: {'validated': True})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
graph.compile()
