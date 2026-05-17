from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    instrument_id: str
    spec_check: bool
    sterility_verified: bool

def validate_specs(state: InstrumentState):
    print(f'Validating specs for {state['instrument_id']}')
    return {'spec_check': True}

def verify_sterility(state: InstrumentState):
    print('Verifying sterile compliance')
    return {'sterility_verified': True}

graph = StateGraph(InstrumentState)
graph.add_node('validate', validate_specs)
graph.add_node('sterility', verify_sterility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterility')
graph.add_edge('sterility', END)
graph = graph.compile()