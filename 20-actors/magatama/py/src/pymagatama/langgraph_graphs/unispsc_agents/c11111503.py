from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class IronOreState(TypedDict):
    sample_id: str
    iron_content: float
    impurities: float
    status: str

def validate_quality(state: IronOreState) -> IronOreState:
    if state['iron_content'] < 60.0 or state['impurities'] > 5.0:
        state['status'] = 'REJECTED'
    else:
        state['status'] = 'APPROVED'
    return state

def logistics_flow(state: IronOreState) -> IronOreState:
    if state['status'] == 'APPROVED':
        state['status'] = 'SHIPPED'
    return state

graph = StateGraph(IronOreState)
graph.add_node('validate', validate_quality)
graph.add_node('logistics', logistics_flow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()