from langgraph.graph import StateGraph
from typing import TypedDict, List

class CastorOilState(TypedDict):
    purity: float
    safety_certs: List[str]
    approved: bool

def validate_quality(state: CastorOilState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_compliance(state: CastorOilState):
    if 'MSDS' not in state['safety_certs']:
        state['approved'] = False
    return state

graph = StateGraph(CastorOilState)
graph.add_node('qc', validate_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('qc')
graph.add_edge('qc', 'compliance')
graph.set_finish_point('compliance')
compiled_graph = graph.compile()