from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AdditiveState(TypedDict):
    purity: float
    compliance_score: float
    messages: Annotated[Sequence[str], operator.add]

def validate_purity(state: AdditiveState) -> AdditiveState:
    if state['purity'] < 0.99:
        return {'messages': ['Purity below threshold, flag for review.']}
    return {'messages': ['Purity verified.']}

def check_compliance(state: AdditiveState) -> AdditiveState:
    if state['compliance_score'] < 0.8:
        return {'messages': ['Compliance failure, halting procurement.']}
    return {'messages': ['Compliance approved.']}

graph = StateGraph(AdditiveState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
