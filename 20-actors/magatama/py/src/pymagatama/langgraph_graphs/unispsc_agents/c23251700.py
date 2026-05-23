from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ForgingMachineState(TypedDict):
    capacity_kn: float
    safety_certs: list[str]
    needs_inspection: bool

def validate_specs(state: ForgingMachineState):
    if state['capacity_kn'] < 1000:
        return {'needs_inspection': False}
    return {'needs_inspection': True}

graph = StateGraph(ForgingMachineState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
