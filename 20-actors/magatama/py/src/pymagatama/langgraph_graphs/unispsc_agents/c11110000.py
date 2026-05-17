from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RawMaterialState(TypedDict):
    material_code: str
    purity: float
    origin: str
    validated: bool
    compliance_report: List[str]

def validate_ore_purity(state: RawMaterialState):
    state['validated'] = state['purity'] >= 95.0
    return state

def check_compliance(state: RawMaterialState):
    if not state['validated']:
        state['compliance_report'].append('Purity check failed for material')
    return state

graph = StateGraph(RawMaterialState)
graph.add_node('validate', validate_ore_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()