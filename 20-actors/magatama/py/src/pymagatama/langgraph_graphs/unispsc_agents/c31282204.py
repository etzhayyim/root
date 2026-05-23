from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BronzeComponentState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: BronzeComponentState):
    required = ['material_grade', 'dimensions']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def process_procurement(state: BronzeComponentState):
    if state['validated']:
        print('Proceeding to supplier RFQ.')
    return state

graph = StateGraph(BronzeComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
