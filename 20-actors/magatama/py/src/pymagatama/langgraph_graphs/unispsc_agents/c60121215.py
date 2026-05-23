from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintState(TypedDict):
    viscosity: float
    peelable: bool
    compliant: bool

def validate_paint_specs(state: PaintState):
    valid = state['viscosity'] < 500 and state['peelable'] is True
    return {'compliant': valid}

def finalize_order(state: PaintState):
    return {'compliant': True}

graph = StateGraph(PaintState)
graph.add_node('validate', validate_paint_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
