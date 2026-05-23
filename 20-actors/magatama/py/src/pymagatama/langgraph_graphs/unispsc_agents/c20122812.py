from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SensorProcurementState(TypedDict):
    sensor_id: str
    specifications: dict
    validation_results: List[str]
    is_approved: bool

def validate_sensor_specs(state: SensorProcurementState):
    specs = state['specifications']
    results = []
    if specs.get('ip_rating', 0) < 65:
        results.append('Insufficient IP rating for industrial use')
    return {'validation_results': results, 'is_approved': len(results) == 0}

def route_procurement(state: SensorProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(SensorProcurementState)
graph.add_node('validate', validate_sensor_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
