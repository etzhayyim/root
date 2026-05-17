from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    purity_level: float
    hazard_rating: int
    analysis_complete: bool
    messages: Annotated[Sequence[str], add_messages]

def validate_composition(state: MineralState):
    if state['purity_level'] < 0.99:
        return {'messages': ['Composition purity below threshold. Re-analysis required.']}
    return {'analysis_complete': True}

def process_hazard_check(state: MineralState):
    if state['hazard_rating'] > 3:
        return {'messages': ['High hazard detected. Route to safety officer.']}
    return {'messages': ['Hazard assessment passed. Proceed to procurement.']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_composition)
graph.add_node('safety', process_hazard_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()