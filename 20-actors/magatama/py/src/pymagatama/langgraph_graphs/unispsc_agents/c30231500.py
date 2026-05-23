from typing import TypedDict
from langgraph.graph import StateGraph, END

class BleacherState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_structural_data(state: BleacherState):
    required = ['load_capacity', 'fire_rating']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def safety_compliance_check(state: BleacherState):
    if state['is_approved']:
        print('Structural integrity verified.')
    return state

graph = StateGraph(BleacherState)
graph.add_node('validate', validate_structural_data)
graph.add_node('safety', safety_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
