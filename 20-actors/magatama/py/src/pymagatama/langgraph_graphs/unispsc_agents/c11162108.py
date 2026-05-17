from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiCProcessState(TypedDict):
    material_id: str
    purity_level: float
    particle_distribution: List[float]
    validation_passed: bool
    log: List[str]

def validate_purity(state: SiCProcessState):
    passed = state['purity_level'] >= 99.9
    return {'validation_passed': passed, 'log': state['log'] + [f'Purity check: {passed}']}

def process_distribution(state: SiCProcessState):
    if not state['validation_passed']:
        return state
    return {'log': state['log'] + ['Distribution verified against standard grade requirements']}

graph = StateGraph(SiCProcessState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('process_distribution', process_distribution)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'process_distribution')
graph.add_edge('process_distribution', END)

app = graph.compile()