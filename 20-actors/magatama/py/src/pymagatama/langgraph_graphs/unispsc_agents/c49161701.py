from typing import TypedDict
from langgraph.graph import StateGraph, END

class JavelinState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: JavelinState):
    required = ['weight', 'length', 'certification']
    valid = all(k in state['specs'] for k in required)
    return {'is_compliant': valid}

def process_procurement(state: JavelinState):
    print('Processing Javelin technical compliance...')
    return {'is_compliant': True}

graph = StateGraph(JavelinState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()