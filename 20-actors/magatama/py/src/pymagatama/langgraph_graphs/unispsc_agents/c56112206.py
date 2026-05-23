from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeskingPartsState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool

def validate_specs(state: DeskingPartsState):
    # Business logic for checking structural and ergonomic specifications
    is_valid = all(key in state['specs'] for key in ['load_limit', 'material', 'dimensions'])
    print(f'Validating parts for ID: {state['part_id']}')
    return {'validation_passed': is_valid}

def process_procurement(state: DeskingPartsState):
    if state['validation_passed']:
        print('Procurement request moving to supplier submission.')
    else:
        print('Specifications incomplete, triggering request for clarification.')
    return {}

graph = StateGraph(DeskingPartsState)
graph.add_node('validate', validate_specs)
graph.add_node('submit', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'submit')
graph.add_edge('submit', END)
graph = graph.compile()
