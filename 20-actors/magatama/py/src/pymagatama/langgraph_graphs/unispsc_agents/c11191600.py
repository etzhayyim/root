from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class MineralState(TypedDict):
    commodity_code: str
    purity_level: float
    origin_docs: Sequence[str]
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: MineralState):
    if state['purity_level'] < 95.0:
        return {'validation_log': ['Low purity detected: manual review required']}
    return {'validation_log': ['Purity check passed']}

def verify_origin(state: MineralState):
    if not state['origin_docs']:
        return {'validation_log': ['Missing origin documentation']}
    return {'validation_log': ['Origin verified successfully']}

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_origin', verify_origin)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_origin')
graph.add_edge('verify_origin', END)
graph = graph.compile()