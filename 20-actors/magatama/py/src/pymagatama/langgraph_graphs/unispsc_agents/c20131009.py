from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PlasticState(TypedDict):
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: PlasticState):
    specs = state['specs']
    logs = []
    if 'tensile_strength_mpa' not in specs:
        logs.append('Missing tensile strength')
    return {'validation_log': logs, 'is_approved': len(logs) == 0}

def approval_node(state: PlasticState):
    return {'is_approved': state['is_approved']}

builder = StateGraph(PlasticState)
builder.add_node('validate', validate_specs)
builder.add_node('approve', approval_node)
builder.add_edge('validate', 'approve')
builder.add_edge('approve', END)
builder.set_entry_point('validate')
graph = builder.compile()