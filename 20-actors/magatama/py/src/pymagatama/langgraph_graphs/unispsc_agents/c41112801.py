from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SpeedometerState(TypedDict):
    part_number: str
    calibration_data: dict
    approved: bool

def validate_calibration(state: SpeedometerState):
    print(f'Validating sensor calibration for {state["part_number"]}')
    return {'approved': True}

def check_compliance(state: SpeedometerState):
    print('Checking regulatory compliance for display protocols')
    return {'approved': state['approved'] and True}

graph = StateGraph(SpeedometerState)
graph.add_node('validate', validate_calibration)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
