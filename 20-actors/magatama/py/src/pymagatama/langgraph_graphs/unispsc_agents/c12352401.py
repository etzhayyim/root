from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SiliconState(TypedDict):
    purity: float
    cas: str
    compliance_checked: bool

def validate_silicon_purity(state: SiliconState):
    if state['purity'] < 99.999:
        return {'compliance_checked': False}
    return {'compliance_checked': True}

def process_deployment(state: SiliconState):
    return {'compliance_checked': True}

graph = StateGraph(SiliconState)
graph.add_node('validate', validate_silicon_purity)
graph.add_node('process', process_deployment)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
