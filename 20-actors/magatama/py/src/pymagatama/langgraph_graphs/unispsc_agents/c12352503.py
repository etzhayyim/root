from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ResinProcessingState(TypedDict):
    resin_id: str
    viscosity: float
    curing_temp: float
    validation_passed: bool
    log: Annotated[Sequence[str], add_messages]

def validate_viscosity(state: ResinProcessingState):
    if 500 <= state['viscosity'] <= 2000:
        return {'validation_passed': True, 'log': ['Viscosity validated']}
    return {'validation_passed': False, 'log': ['Viscosity out of spec']}

def route_by_validation(state: ResinProcessingState):
    return 'process' if state['validation_passed'] else END

def process_resin(state: ResinProcessingState):
    return {'log': [f'Processing at {state['curing_temp']}C']}

graph = StateGraph(ResinProcessingState)
graph.add_node('validate', validate_viscosity)
graph.add_node('process', process_resin)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
graph = graph.compile()