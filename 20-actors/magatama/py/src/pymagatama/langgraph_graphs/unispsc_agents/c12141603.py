from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class InorganicProcessState(TypedDict):
    purity_level: float
    particle_size_micron: float
    validation_passed: bool
    log: List[str]

def validate_purity(state: InorganicProcessState):
    passed = state['purity_level'] >= 99.9
    return {'validation_passed': passed, 'log': [f'Purity check: {passed}']}

def check_particle_specs(state: InorganicProcessState):
    passed = 0.5 <= state['particle_size_micron'] <= 50.0
    return {'validation_passed': passed and state['validation_passed'], 'log': state['log'] + [f'Particle spec check: {passed}']}

graph = StateGraph(InorganicProcessState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_particle', check_particle_specs)
graph.add_edge('validate_purity', 'check_particle')
graph.add_edge('check_particle', END)
graph.set_entry_point('validate_purity')
compiled_graph = graph.compile()
