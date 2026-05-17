from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoilState(TypedDict):
    inductance: float
    thermal_class: str
    is_compliant: bool

def validate_coil_specs(state: CoilState):
    # Business logic for motor coil safety validation
    compliant = state['inductance'] > 0 and state['thermal_class'] in ['F', 'H']
    return {'is_compliant': compliant}

workflow = StateGraph(CoilState)
workflow.add_node('validation', validate_coil_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()