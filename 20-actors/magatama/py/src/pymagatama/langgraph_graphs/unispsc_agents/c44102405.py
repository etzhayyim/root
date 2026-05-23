from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabelMachineState(TypedDict):
    model: str
    resolution: int
    is_compliant: bool

def validate_specs(state: LabelMachineState):
    state['is_compliant'] = state['resolution'] >= 200
    return 'compliant' if state['is_compliant'] else 'non-compliant'

graph = StateGraph(LabelMachineState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
