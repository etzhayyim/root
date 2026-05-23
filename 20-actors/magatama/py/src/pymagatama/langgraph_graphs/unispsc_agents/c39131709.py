from typing import TypedDict
from langgraph.graph import StateGraph, END

class RacewayState(TypedDict):
    specs: dict
    validation_result: bool
    compliance_report: str

def validate_raceway_specs(state: RacewayState):
    required = ['fire_rating', 'material']
    valid = all(k in state['specs'] for k in required)
    return {'validation_result': valid, 'compliance_report': 'Validated' if valid else 'Missing specs'}

def generate_procurement_workflow(state: RacewayState):
    return {'compliance_report': f'Workflow generated for {state.get("specs")}'}

graph = StateGraph(RacewayState)
graph.add_node('validate', validate_raceway_specs)
graph.add_node('generate', generate_procurement_workflow)
graph.add_edge('validate', 'generate')
graph.add_edge('generate', END)
graph.set_entry_point('validate')
graph = graph.compile()
