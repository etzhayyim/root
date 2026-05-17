from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_load_capacity(state: BearingState):
    load = state['spec_data'].get('load', 0)
    res = 'Valid' if load > 0 else 'Invalid: Capacity missing'
    return {'validation_results': [res], 'is_compliant': load > 0}

def check_compliance(state: BearingState):
    return 'compliant' if state.get('is_compliant', False) else 'non_compliant'

graph = StateGraph(BearingState)
graph.add_node('validate', validate_load_capacity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')