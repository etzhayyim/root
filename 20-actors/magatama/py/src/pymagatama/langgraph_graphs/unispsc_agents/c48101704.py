from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PumpState(TypedDict):
    pump_material: str
    flow_accuracy: float
    food_certified: bool
    validation_log: List[str]

def validate_material(state: PumpState):
    valid = state['pump_material'] in ['Food Grade Polypropylene', 'Stainless Steel 304']
    return {'validation_log': [f'Material validation: {valid}']}

def check_compliance(state: PumpState):
    status = 'Pass' if state['food_certified'] and state['flow_accuracy'] > 0.95 else 'Fail'
    return {'validation_log': state['validation_log'] + [f'Compliance: {status}']}

graph_builder = StateGraph(PumpState)
graph_builder.add_node('validate', validate_material)
graph_builder.add_node('compliance', check_compliance)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'compliance')
graph_builder.add_edge('compliance', END)
graph = graph_builder.compile()
