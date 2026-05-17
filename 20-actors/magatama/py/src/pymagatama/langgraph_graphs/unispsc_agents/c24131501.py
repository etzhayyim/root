from typing import TypedDict
from langgraph.graph import StateGraph, END

class RefrigeratorState(TypedDict):
    specs: dict
    validation_error: str
    is_compliant: bool

def validate_specs(state: RefrigeratorState):
    required = ['Energy Efficiency Rating', 'Capacity', 'Refrigerant']
    is_ok = all(k in state['specs'] for k in required)
    return {'is_compliant': is_ok, 'validation_error': None if is_ok else 'Missing mandatory specs'}

def process_procurement(state: RefrigeratorState):
    if state['is_compliant']:
        print('Proceeding to procurement approval...')
    return state

graph = StateGraph(RefrigeratorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()