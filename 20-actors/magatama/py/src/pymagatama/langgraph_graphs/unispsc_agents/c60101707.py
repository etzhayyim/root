from typing import TypedDict
from langgraph.graph import StateGraph, END

class CurriculumState(TypedDict):
    doc_content: str
    compliance_score: float
    validation_notes: list[str]

def validate_curriculum(state: CurriculumState):
    score = 0.0
    notes = []
    if len(state['doc_content']) > 100:
        score = 0.8
        notes.append('Content length sufficient for curriculum review.')
    else:
        notes.append('Content insufficient for pedagogical verification.')
    return {'compliance_score': score, 'validation_notes': notes}

graph = StateGraph(CurriculumState)
graph.add_node('validate', validate_curriculum)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()