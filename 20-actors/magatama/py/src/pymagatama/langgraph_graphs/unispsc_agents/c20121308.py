from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ServoProcState(TypedDict):
    specs: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: ServoProcState):
    torque = state['specs'].get('rated_torque', 0)
    if torque > 0:
        return {'validation_results': ['Torque spec validated']}
    return {'validation_results': ['Invalid torque spec']}

def check_compliance(state: ServoProcState):
    is_compliant = state['specs'].get('ip_rating', 0) >= 54
    return {'is_approved': is_compliant}

graph = StateGraph(ServoProcState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()