from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ProcessorState(TypedDict):
    task_id: str
    data_load: float
    process_log: Annotated[Sequence[str], operator.add]
    is_validated: bool

def validate_load(state: ProcessorState) -> ProcessorState:
    # Logic to validate system load capacity before processing
    state['is_validated'] = state['data_load'] < 95.0
    state['process_log'] = [f'Load validation: {state['is_validated']}']
    return state

def execute_task(state: ProcessorState) -> ProcessorState:
    # Logic to simulate intensive data processing
    if state['is_validated']:
        state['process_log'] = ['Task execution successful']
    else:
        state['process_log'] = ['Task execution skipped: load too high']
    return state

# Compile Graph
builder = StateGraph(ProcessorState)
builder.add_node('validate', validate_load)
builder.add_node('execute', execute_task)
builder.set_entry_point('validate')
builder.add_edge('validate', 'execute')
builder.add_edge('execute', END)
graph = builder.compile()
