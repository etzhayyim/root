from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FoodState(TypedDict):
    item_name: str
    quality_docs: List[str]
    temp_compliant: bool
    approved: bool

def validate_quality(state: FoodState):
    state['approved'] = 'HACCP' in state['quality_docs'] and state['temp_compliant']
    return state

graph = StateGraph(FoodState)
graph.add_node('qc_check', validate_quality)
graph.set_entry_point('qc_check')
graph.add_edge('qc_check', END)
graph = graph.compile()
