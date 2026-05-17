from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MiningState(TypedDict):
    equipment_id: str
    spec_data: dict
    validation_errors: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: MiningState):
    specs = state['spec_data']
    errors = []
    if 'load_capacity' not in specs or specs['load_capacity'] <= 0:
        errors.append('Invalid load capacity')
    return {'validation_errors': errors}

def approval_node(state: MiningState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(MiningState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()