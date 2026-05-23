from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    sample_id: str
    purity_level: float
    analysis_steps: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_sample(state: MineralProcessState):
    is_valid = state['purity_level'] >= 99.0
    return {'is_compliant': is_valid}

def process_mineral(state: MineralProcessState):
    return {'analysis_steps': ['Standardizing sample', 'XRF analysis', 'Trace element mapping']}

graph = StateGraph(MineralProcessState)
graph.add_node('validate', validate_sample)
graph.add_node('process', process_mineral)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
process_graph = graph.compile()
