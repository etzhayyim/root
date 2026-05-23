from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VectorState(TypedDict):
    vector_id: str
    sequence_data: str
    validation_passed: bool
    compliance_tags: List[str]

def validate_sequence(state: VectorState):
    # Simulate BLAST or sequence alignment check
    is_valid = len(state['sequence_data']) > 0
    return {'validation_passed': is_valid}

def check_compliance(state: VectorState):
    tags = ['dual-use-export-control'] if 'CRISPR' in state['sequence_data'] else []
    return {'compliance_tags': tags}

graph = StateGraph(VectorState)
graph.add_node('validate', validate_sequence)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
