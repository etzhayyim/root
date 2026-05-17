from langgraph.graph import StateGraph, END
from typing import TypedDict

class DuplexerState(TypedDict):
    model_id: str
    validation_passed: bool
    qc_checked: bool

def validate_specs(state: DuplexerState):
    # Perform compatibility check for duplexer module
    state['validation_passed'] = bool(state['model_id'])
    print(f'Validating spec for {state['model_id']}')
    return {'validation_passed': True}

def perform_qc(state: DuplexerState):
    state['qc_checked'] = True
    return {'qc_checked': True}

graph = StateGraph(DuplexerState)
graph.add_node('validate', validate_specs)
graph.add_node('qc', perform_qc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()