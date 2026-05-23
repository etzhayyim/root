from typing import TypedDict
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    item_name: str
    quality_check: bool
    approved: bool

def validate_instrument_specs(state: InstrumentState):
    # Simulate spec verification for musical instruments
    print(f'Validating specs for: {state["item_name"]}')
    return {'quality_check': True}

def approval_step(state: InstrumentState):
    is_approved = state['quality_check'] is True
    return {'approved': is_approved}

graph = StateGraph(InstrumentState)
graph.add_node('validate', validate_instrument_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
