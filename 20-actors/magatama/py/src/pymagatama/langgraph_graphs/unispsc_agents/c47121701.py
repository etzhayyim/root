from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrashBagState(TypedDict):
    spec: dict
    validation_result: bool

def validate_specs(state: TrashBagState):
    # Business logic for trash bag procurement specs
    required_fields = ['thickness', 'capacity', 'material']
    valid = all(key in state['spec'] for key in required_fields)
    return {'validation_result': valid}

def approval_check(state: TrashBagState):
    return 'APPROVED' if state['validation_result'] else 'REJECTED'

graph = StateGraph(TrashBagState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()