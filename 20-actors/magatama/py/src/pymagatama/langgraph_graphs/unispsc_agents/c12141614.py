from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ResinProcessingState(TypedDict):
    purity: float
    viscosity: float
    status: str
    validation_log: Annotated[Sequence[str], add_messages]

def validate_resin_specs(state: ResinProcessingState) -> ResinProcessingState:
    is_valid = state['purity'] >= 99.0 and 50 <= state['viscosity'] <= 500
    return {
        'status': 'VALIDATED' if is_valid else 'REJECTED',
        'validation_log': [f'Validation result: {is_valid}']
    }

def route_for_processing(state: ResinProcessingState) -> str:
    return 'process' if state['status'] == 'VALIDATED' else END

builder = StateGraph(ResinProcessingState)
builder.add_node('validate', validate_resin_specs)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()