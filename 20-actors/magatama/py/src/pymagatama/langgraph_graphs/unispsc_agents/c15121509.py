from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CatalystState(TypedDict):
    purity: float
    activity: float
    validation_log: Annotated[List[str], add_messages]

def validate_purity(state: CatalystState):
    log = 'Purity validated' if state['purity'] >= 99.9 else 'Purity failed'
    return {'validation_log': [log]}

def validate_activity(state: CatalystState):
    log = 'Activity within operational range' if 0.8 <= state['activity'] <= 1.2 else 'Activity outside threshold'
    return {'validation_log': [log]}

graph = StateGraph(CatalystState)
graph.add_node('purity_check', validate_purity)
graph.add_node('activity_check', validate_activity)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'activity_check')
graph.add_edge('activity_check', END)
graph = graph.compile()
