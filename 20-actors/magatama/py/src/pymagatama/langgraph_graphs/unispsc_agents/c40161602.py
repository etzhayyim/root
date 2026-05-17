from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirCleanerState(TypedDict):
    model_number: str
    cadr_value: float
    filter_type: str
    is_compliant: bool

def validate_specs(state: AirCleanerState):
    # Business logic for air cleaner compliance
    compliant = state['cadr_value'] > 100 and state['filter_type'] == 'HEPA'
    return {'is_compliant': compliant}

def approval_step(state: AirCleanerState):
    print(f'Processing procurement for {state['model_number']}')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(AirCleanerState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()