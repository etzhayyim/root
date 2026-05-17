from typing import TypedDict
from langgraph.graph import StateGraph, END

class HumidityState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: HumidityState):
    s = state['specs']
    errors = []
    if s.get('accuracy', 0) > 5.0: errors.append('Low accuracy')
    if not s.get('has_cal_cert', False): errors.append('Missing cert')
    return {'validated': len(errors) == 0, 'error_log': errors}

def finalize_order(state: HumidityState):
    return {'validated': True}

graph = StateGraph(HumidityState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()