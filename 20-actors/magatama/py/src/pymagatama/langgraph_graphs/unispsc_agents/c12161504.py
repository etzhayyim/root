from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    purity: float
    particle_size: float
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_purity(state: MetalPowderState):
    log = ['Purity check passed'] if state['purity'] >= 0.999 else ['Purity check failed']
    return {'validation_log': log}

def inspect_particles(state: MetalPowderState):
    status = 'APPROVED' if 1 <= state['particle_size'] <= 50 else 'REJECTED'
    return {'status': status}

graph = StateGraph(MetalPowderState)
graph.add_node('validate', validate_purity)
graph.add_node('inspect', inspect_particles)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
