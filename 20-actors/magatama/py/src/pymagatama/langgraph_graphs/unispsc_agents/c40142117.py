from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    material_grade: str
    dimensions: dict
    compliance_docs: List[str]
    approved: bool

def validate_material(state: PipeState) -> PipeState:
    # Logic for material grade verification
    state['approved'] = state['material_grade'] in ['SUS304', 'SUS316']
    return state

def check_compliance(state: PipeState) -> PipeState:
    # Logic for certification audit
    if state['approved'] and 'MTR' in state['compliance_docs']:
        state['approved'] = True
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
