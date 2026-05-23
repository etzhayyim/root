from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    capacity: float
    material_spec: str
    is_un_certified: bool
    validation_log: List[str]

def validate_container_specs(state: ContainerState):
    logs = []
    if state['capacity'] <= 0:
        logs.append('Error: Capacity must be positive')
    if state['is_un_certified'] and not state['material_spec']:
        logs.append('Warning: UN certification requires material specification')
    return {'validation_log': logs}

def route_by_validation(state: ContainerState):
    return 'validate' if not state['validation_log'] else END

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_container_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile = graph.compile()
