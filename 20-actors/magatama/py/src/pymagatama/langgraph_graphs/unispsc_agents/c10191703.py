from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class MineProcessState(TypedDict):
    throughput: float
    status: str
    validation_errors: list[str]

def validate_throughput(state: MineProcessState) -> MineProcessState:
    if state['throughput'] <= 0:
        state['validation_errors'].append('Invalid throughput')
    return state

def process_ore(state: MineProcessState) -> MineProcessState:
    state['status'] = 'processed'
    return state

graph = StateGraph(MineProcessState)
graph.add_node('validate', validate_throughput)
graph.add_node('process', process_ore)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
