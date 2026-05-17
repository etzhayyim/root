from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CharcoalProcurementState(TypedDict):
    commodity_code: str
    spec_requirements: dict
    validation_logs: List[str]
    approved: bool

def validate_fuel_quality(state: CharcoalProcurementState) -> CharcoalProcurementState:
    specs = state['spec_requirements']
    logs = state['validation_logs']
    if specs.get('calorific_value_kcal', 0) > 7000:
        logs.append('Calorific value acceptable for mining industrial use.')
    else:
        logs.append('Calorific value insufficient.')
    state['approved'] = specs.get('calorific_value_kcal', 0) > 7000
    return state

graph = StateGraph(CharcoalProcurementState)
graph.add_node('validate', validate_fuel_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()