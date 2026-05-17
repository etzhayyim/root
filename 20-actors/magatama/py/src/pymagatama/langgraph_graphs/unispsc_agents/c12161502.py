from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    material_id: str
    purity: float
    activity_score: float
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState):
    log = ['Purity check initiated']
    if state['purity'] < 0.99:
        log.append('Purity below 99% threshold - flagging for review')
    return {'validation_log': log}

def analyze_activity(state: CatalystState):
    log = ['Activity evaluation performed']
    return {'validation_log': log}

graph = StateGraph(CatalystState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('analyze_activity', analyze_activity)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'analyze_activity')
graph.add_edge('analyze_activity', END)
graph = graph.compile()