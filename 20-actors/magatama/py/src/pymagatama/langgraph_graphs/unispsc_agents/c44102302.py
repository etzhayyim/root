from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PackagingState(TypedDict):
    machine_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: PackagingState):
    errors = []
    if 'max_dims' not in state['machine_specs']: errors.append('Missing dimensions')
    if 'speed' not in state['machine_specs']: errors.append('Missing speed rating')
    return {"validation_errors": errors, "is_compliant": len(errors) == 0}

def route_by_compliance(state: PackagingState):
    return 'compliant' if state['is_compliant'] else 'review'

graph = StateGraph(PackagingState)
graph.add_node('validator', validate_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
graph = graph.compile()
