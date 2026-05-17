from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    items: List[str]
    validated: bool
    compliance_report: str

def validate_fasteners(state: FastenerState):
    validated = all(len(item) > 0 for item in state['items'])
    return {'validated': validated, 'compliance_report': 'Validated' if validated else 'Missing data'}

def route_by_validation(state: FastenerState):
    return 'process' if state['validated'] else END

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_fasteners)
graph.set_entry_point('validate')
graph.add_edge('validate', END)