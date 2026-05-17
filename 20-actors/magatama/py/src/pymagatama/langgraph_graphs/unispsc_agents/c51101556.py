from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    temperature_logs: Annotated[Sequence[float], operator.add]
    is_compliant: bool

def validate_cold_chain(state: PharmState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs']) if state['temperature_logs'] else 25.0
    return {'is_compliant': 2.0 <= avg_temp <= 8.0}

def process_batch(state: PharmState):
    print(f'Processing batch {state['batch_id']}: Compliance={state['is_compliant']}')
    return state

builder = StateGraph(PharmState)
builder.add_node('validate', validate_cold_chain)
builder.add_node('process', process_batch)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()