from typing import TypedDict
from langgraph.graph import StateGraph, END

class DataState(TypedDict):
    raw_data: dict
    validated_data: dict
    calculation_result: float

def validate_sensor_data(state: DataState):
    data = state['raw_data']
    return {'validated_data': {k: v for k, v in data.items() if v is not None}}

def process_evaporation_metrics(state: DataState):
    val = state['validated_data']
    return {'calculation_result': val.get('current', 0.0)}

graph = StateGraph(DataState)
graph.add_node('validate', validate_sensor_data)
graph.add_node('calculate', process_evaporation_metrics)
graph.add_edge('validate', 'calculate')
graph.add_edge('calculate', END)
graph.set_entry_point('validate')
graph = graph.compile()
