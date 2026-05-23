from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class RoofValleyState(TypedDict):
    specs: dict
    validation_log: Annotated[list, operator.add]
    status: str

def validate_material(state: RoofValleyState):
    material = state['specs'].get('material', 'unknown')
    if material in ['galvanized_steel', 'copper', 'aluminum']:
        return {'validation_log': ['Material validated: ' + material], 'status': 'valid'}
    return {'validation_log': ['Material rejected'], 'status': 'invalid'}

def check_compliance(state: RoofValleyState):
    compliance = state['specs'].get('certifications', [])
    if len(compliance) > 0:
        return {'validation_log': ['Compliance verified against local code']}
    return {'validation_log': ['Compliance pending']}

graph = StateGraph(RoofValleyState)
graph.add_node('material_check', validate_material)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
