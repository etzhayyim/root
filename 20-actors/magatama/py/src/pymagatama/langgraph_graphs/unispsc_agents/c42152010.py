from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalFilmState(TypedDict):
    product_id: str
    compliance_checks: List[str]
    approved: bool

def validate_certification(state: DentalFilmState):
    state['compliance_checks'].append('ISO-13485-checked')
    return state

def check_storage_requirements(state: DentalFilmState):
    state['compliance_checks'].append('temp-control-verified')
    return state

graph = StateGraph(DentalFilmState)
graph.add_node('cert', validate_certification)
graph.add_node('storage', check_storage_requirements)
graph.set_entry_point('cert')
graph.add_edge('cert', 'storage')
graph.add_edge('storage', END)
graph = graph.compile()