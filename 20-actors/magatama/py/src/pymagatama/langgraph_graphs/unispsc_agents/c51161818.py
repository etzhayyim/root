from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity: float
    compliance_checked: bool

def validate_purity(state: PharmState):
    if state['purity'] < 99.0:
        raise ValueError('Purity below pharmaceutical threshold')
    return {'compliance_checked': True}

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()