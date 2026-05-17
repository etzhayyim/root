from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class MaterialState(TypedDict):
    material_code: str
    purity_level: float
    inspection_passed: bool
    logs: Annotated[List[str], operator.add]

def validate_material(state: MaterialState):
    if state['purity_level'] >= 99.9:
        return {'inspection_passed': True, 'logs': ['Purity validation passed']}
    else:
        return {'inspection_passed': False, 'logs': ['Purity below threshold']}

def process_procurement(state: MaterialState):
    if state['inspection_passed']:
        return {'logs': ['Proceeding with procurement order']}
    return {'logs': ['Procurement halted due to quality failure']}

graph = StateGraph(MaterialState)
graph.add_node('validate', validate_material)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()