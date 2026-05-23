from typing import TypedDict
from langgraph.graph import StateGraph, END
class PaintState(TypedDict):
    spec_sheet: dict
    approved: bool
def validate_safety_data(state: PaintState):
    content = state['spec_sheet']
    is_compliant = content.get('flash_point', 0) > 0 and content.get('voc_level', 999) < 500
    return {'approved': is_compliant}
def create_graph():
    graph = StateGraph(PaintState)
    graph.add_node('safety_check', validate_safety_data)
    graph.set_entry_point('safety_check')
    graph.add_edge('safety_check', END)
    return graph.compile()
graph = create_graph()
