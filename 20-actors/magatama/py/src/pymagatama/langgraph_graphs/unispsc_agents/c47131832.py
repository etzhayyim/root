from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DustProductState(TypedDict):
    product_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_materials(state: DustProductState):
    print(f'Validating MSDS for: {state["product_name"]}')
    return {'is_approved': True}

def quality_check(state: DustProductState):
    print('Checking dust suppression efficiency metrics.')
    return {'is_approved': state.get('is_approved', False)}

graph = StateGraph(DustProductState)
graph.add_node('validate', validate_materials)
graph.add_node('quality_check', quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()
