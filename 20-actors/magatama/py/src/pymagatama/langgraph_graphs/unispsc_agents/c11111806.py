from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiCState(TypedDict):
    purity: float
    particle_size: float
    validated: bool
    logs: List[str]

def validate_purity(state: SiCState) -> SiCState:
    if state['purity'] >= 99.5:
        state['validated'] = True
        state['logs'].append('Purity check passed')
    else:
        state['validated'] = False
        state['logs'].append('Purity check failed')
    return state

def check_particle_specs(state: SiCState) -> SiCState:
    if 0.1 <= state['particle_size'] <= 50.0:
        state['logs'].append('Particle size within tolerance')
    else:
        state['logs'].append('Particle size out of spec')
    return state

builder = StateGraph(SiCState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_particle', check_particle_specs)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_particle')
builder.add_edge('check_particle', END)
graph = builder.compile()
