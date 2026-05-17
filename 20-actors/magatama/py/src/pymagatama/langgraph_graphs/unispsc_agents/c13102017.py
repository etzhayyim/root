from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    material_id: str
    purity_level: float
    validation_logs: List[str]
    is_approved: bool

def validate_purity(state: MineralProcessState):
    if state['purity_level'] >= 99.5:
        state['validation_logs'].append('Purity check passed.')
        return {'is_approved': True}
    state['validation_logs'].append('Purity check failed.')
    return {'is_approved': False}

def process_batch(state: MineralProcessState):
    state['validation_logs'].append('Batch processing initiated.')
    return state

graph = StateGraph(MineralProcessState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_batch)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()