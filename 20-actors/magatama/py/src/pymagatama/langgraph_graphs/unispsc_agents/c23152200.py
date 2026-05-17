from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TableSpecState(TypedDict):
    material: str
    load_capacity: float
    dimensions: dict
    is_compliant: bool

def validate_specs(state: TableSpecState):
    if state['load_capacity'] > 0 and state['material']:
        return {'is_compliant': True}
    return {'is_compliant': False}

def route_by_compliance(state: TableSpecState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(TableSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'reject': END})
app = graph.compile()