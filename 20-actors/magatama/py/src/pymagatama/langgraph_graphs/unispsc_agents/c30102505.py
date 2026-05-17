from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteelSpecState(TypedDict):
    material_grade: str
    dimensions: str
    compliance_docs: List[str]
    validated: bool

def validate_material(state: SteelSpecState):
    # Business logic for stainless steel validation
    is_valid = state['material_grade'] in ['SUS304', 'SUS316', 'SUS430']
    return {'validated': is_valid}

def process_procurement(state: SteelSpecState):
    print(f'Processing procurement of grade {state["material_grade"]}')
    return {'validated': True}

graph = StateGraph(SteelSpecState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()