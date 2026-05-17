from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BiologicalState(TypedDict):
    specimen_id: str
    quarantine_status: bool
    viability_score: float
    log: Annotated[Sequence[str], operator.add]

def validate_biota(state: BiologicalState):
    # Simulate biological validation
    if state['viability_score'] < 0.8:
        return {'log': ['Validation failed: low viability score']}
    return {'log': ['Biological validation passed'], 'quarantine_status': True}

def process_quarantine(state: BiologicalState):
    if state['quarantine_status']:
        return {'log': ['Release from quarantine authorized']}
    return {'log': ['Quarantine hold initiated']}

graph = StateGraph(BiologicalState)
graph.add_node('validate', validate_biota)
graph.add_node('quarantine', process_quarantine)
graph.add_edge('validate', 'quarantine')
graph.add_edge('quarantine', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()