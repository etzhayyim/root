from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ComponentState(TypedDict):
    part_id: str
    specs: dict
    validation_logs: List[str]
    is_approved: bool

def validate_specs(state: ComponentState) -> ComponentState:
    specs = state['specs']
    logs = []
    if 'voltage_rating' not in specs:
        logs.append('Missing voltage rating')
    state['validation_logs'] = logs
    state['is_approved'] = len(logs) == 0
    return state

def compile_component_workflow():
    workflow = StateGraph(ComponentState)
    workflow.add_node('validate', validate_specs)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_component_workflow()