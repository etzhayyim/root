from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ModelingDoughState(TypedDict):
    safety_check: bool
    compliance_docs: List[str]
    approved: bool

def validate_safety(state: ModelingDoughState):
    state['safety_check'] = all(doc in state['compliance_docs'] for doc in ['ASTM_D4236', 'NonToxic_Cert'])
    return state

def determine_approval(state: ModelingDoughState):
    state['approved'] = state['safety_check']
    return 'end'

graph = StateGraph(ModelingDoughState)
graph.add_node('safety', validate_safety)
graph.add_edge('safety', END)
graph.set_entry_point('safety')
