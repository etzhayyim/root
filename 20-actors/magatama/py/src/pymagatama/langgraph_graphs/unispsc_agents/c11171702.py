from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MetalOxideState(TypedDict):
    purity_level: float
    particle_size: float
    validation_logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: MetalOxideState):
    log = 'Purity validated' if state['purity_level'] >= 99.5 else 'Purity failed'
    return {'validation_logs': [log]}

def check_particle_size(state: MetalOxideState):
    log = 'Size within range' if 1.0 <= state['particle_size'] <= 50.0 else 'Size out of spec'
    return {'validation_logs': [log]}

graph = StateGraph(MetalOxideState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_particle_size', check_particle_size)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_particle_size')
graph.add_edge('check_particle_size', END)
compiled_graph = graph.compile()