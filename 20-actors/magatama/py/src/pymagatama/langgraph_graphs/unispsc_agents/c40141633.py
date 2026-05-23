from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    specs: dict
    validated: bool
    error_log: List[str]

def validate_specs(state: ValveState) -> ValveState:
    required = ['pressure_rating', 'material', 'actuation']
    missing = [f for f in required if f not in state['specs']]
    if missing:
        state['error_log'] = [f'Missing specs: {missing}']
        state['validated'] = False
    else:
        state['validated'] = True
    return state

def route_by_validation(state: ValveState) -> str:
    return 'process' if state['validated'] else 'reject'

graph = StateGraph(ValveState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, 'reject': END})
graph.compile()
