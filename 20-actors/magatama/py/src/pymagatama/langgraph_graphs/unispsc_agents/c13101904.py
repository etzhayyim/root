from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CarbonFiberState(TypedDict):
    spec: dict
    validation_results: Annotated[List[str], operator.add]
    is_cleared: bool

def validate_tensile_modulus(state: CarbonFiberState):
    modulus = state['spec'].get('tensile_modulus_gpa', 0)
    if modulus >= 230:
        return {'validation_results': ['Modulus check passed'], 'is_cleared': True}
    return {'validation_results': ['Modulus check failed'], 'is_cleared': False}

def check_dual_use(state: CarbonFiberState):
    if state['spec'].get('tensile_modulus_gpa', 0) > 400:
        return {'validation_results': ['High-performance export license required']}
    return {'validation_results': ['Export assessment complete']}

graph = StateGraph(CarbonFiberState)
graph.add_node('validate_modulus', validate_tensile_modulus)
graph.add_node('check_dual_use', check_dual_use)
graph.set_entry_point('validate_modulus')
graph.add_edge('validate_modulus', 'check_dual_use')
graph.add_edge('check_dual_use', END)
app = graph.compile()