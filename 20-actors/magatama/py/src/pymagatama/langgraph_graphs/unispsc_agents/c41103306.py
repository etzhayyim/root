from typing import TypedDict
from langgraph.graph import StateGraph, END

class VacuumSystemState(TypedDict):
    pressure: float
    flow_rate: float
    is_compliant: bool

def validate_specs(state: VacuumSystemState):
    if state['pressure'] > 0.7:
        return {'is_compliant': False}
    return {'is_compliant': True}

graph = StateGraph(VacuumSystemState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
