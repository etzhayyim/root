from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    safety_clearance: bool
    steps: List[str]

def validate_chemical(state: ChemicalState):
    if state['purity'] < 99.9:
        return {'steps': state['steps'] + ['Refining requested']}
    return {'safety_clearance': True, 'steps': state['steps'] + ['Purity validated']}

def export_review(state: ChemicalState):
    if state.get('safety_clearance'):
        return {'steps': state['steps'] + ['Export control cleared']}
    return {'steps': state['steps'] + ['Export hold']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_chemical)
graph.add_node('export', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
