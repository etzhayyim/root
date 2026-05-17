from typing import TypedDict
from langgraph.graph import StateGraph, END

class TableState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: TableState):
    required = ['height', 'load_capacity', 'antibacterial_rating']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def check_medical_grade(state: TableState):
    print('Checking clinical compliance...')
    return {'is_compliant': state['is_compliant'] and state['specs'].get('certified')}

graph = StateGraph(TableState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_medical_grade)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()