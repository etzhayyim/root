from langgraph.graph import StateGraph, END
from typing import TypedDict
class FilterSpecState(TypedDict):
    spec: dict
    validated: bool
def validate_materials(state: FilterSpecState):
    material = state['spec'].get('membrane_material')
    state['validated'] = material is not None and len(material) > 0
    return state
def check_pore_size(state: FilterSpecState):
    size = state['spec'].get('pore_size_microns', 0)
    if size <= 0: state['validated'] = False
    return state
graph = StateGraph(FilterSpecState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_pore_size', check_pore_size)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_pore_size')
graph.add_edge('check_pore_size', END)
app = graph.compile()
