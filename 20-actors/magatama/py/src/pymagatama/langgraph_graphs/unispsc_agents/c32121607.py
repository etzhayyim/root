from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ResistorState(TypedDict):
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ResistorState):
    required = ['resistance', 'tolerance', 'power_rating']
    errors = [f'Missing {f}' for f in required if f not in state['specifications']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: ResistorState):
    if state['validation_passed']:
        print('Proceeding to supplier RFQ phase.')
    return {'status': 'processed'}

graph = StateGraph(ResistorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
