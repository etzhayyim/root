from langgraph.graph import StateGraph, END
from typing import TypedDict
class MaterialState(TypedDict):
    content_id: str
    validation_passed: bool
    is_digital: bool
def validate_material(state: MaterialState):
    print(f'Validating material: {state['content_id']}')
    return {'validation_passed': True}
def process_delivery(state: MaterialState):
    return {'validation_passed': True}
graph = StateGraph(MaterialState)
graph.add_node('validate', validate_material)
graph.add_node('delivery', process_delivery)
graph.set_entry_point('validate')
graph.add_edge('validate', 'delivery')
graph.add_edge('delivery', END)
graph = graph.compile()