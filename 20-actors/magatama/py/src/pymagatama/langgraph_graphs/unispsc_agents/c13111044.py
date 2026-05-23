from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    material_id: str
    purity_level: float
    safety_check_passed: bool
    messages: Annotated[List[str], add_messages]

def validate_purity(state: MineralState):
    passed = state['purity_level'] >= 99.9
    return {'safety_check_passed': passed}

def process_logistics(state: MineralState):
    return {'messages': ['Logistics workflow initiated for hazardous mineral handling.']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', process_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
app = graph.compile()
