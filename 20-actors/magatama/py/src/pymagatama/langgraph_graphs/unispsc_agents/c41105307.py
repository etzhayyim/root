from typing import TypedDict
from langgraph.graph import StateGraph, END

class CEState(TypedDict):
    instrument_id: str
    validation_status: str
    calibration_passed: bool

def validate_instrument(state: CEState):
    print(f'Validating: {state[\'instrument_id\']}')
    return {'validation_status': 'passed', 'calibration_passed': True}

def finalize_procurement(state: CEState):
    print('Procurement logic finalized.')
    return {'validation_status': 'completed'}

graph = StateGraph(CEState)
graph.add_node('validate', validate_instrument)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()