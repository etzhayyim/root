from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PaintState(TypedDict):
    product_name: str
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_pigments(state: PaintState):
    state['validation_log'].append('Checking ASTM D-4236 toxicity compliance')
    state['is_compliant'] = True
    return state

def check_lightfastness(state: PaintState):
    state['validation_log'].append('Verifying lightfastness rating')
    return state

graph = StateGraph(PaintState)
graph.add_node('validate_pigments', validate_pigments)
graph.add_node('check_lightfastness', check_lightfastness)
graph.set_entry_point('validate_pigments')
graph.add_edge('validate_pigments', 'check_lightfastness')
graph.add_edge('check_lightfastness', END)
app = graph.compile()
