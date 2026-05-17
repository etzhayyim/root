from typing import TypedDict
from langgraph.graph import StateGraph, END
class SoftwareProcurementState(TypedDict):
    license_type: str
    os_compatibility: list[str]
    validation_status: bool
def validate_specs(state: SoftwareProcurementState):
    state['validation_status'] = len(state['os_compatibility']) > 0
    return state
graph = StateGraph(SoftwareProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()