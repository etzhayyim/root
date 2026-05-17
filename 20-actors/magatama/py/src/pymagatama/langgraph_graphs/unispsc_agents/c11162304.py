from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    batch_id: str
    purity_level: float
    particle_distribution: List[float]
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_purity(state: AbrasiveState) -> AbrasiveState:
    compliant = state['purity_level'] >= 99.5
    return {'is_compliant': compliant, 'validation_logs': ['Purity check passed' if compliant else 'Purity failed']}

def process_distribution(state: AbrasiveState) -> AbrasiveState:
    avg_dist = sum(state['particle_distribution']) / len(state['particle_distribution'])
    log = f'Distribution validated with avg: {avg_dist}'
    return {'validation_logs': [log]}

graph = StateGraph(AbrasiveState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('process_distribution', process_distribution)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'process_distribution')
graph.add_edge('process_distribution', END)
graph = graph.compile()