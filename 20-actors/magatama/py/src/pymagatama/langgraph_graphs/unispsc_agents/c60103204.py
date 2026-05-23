from langgraph.graph import StateGraph, END
from typing import TypedDict
import json

class AuditState(TypedDict):
    product_data: dict
    approved: bool
    validation_log: list

def validate_specs(state: AuditState):
    required = ['material_safety', 'age_rating']
    logs = [key for key in required if key not in state['product_data']]
    return {'validation_log': logs, 'approved': len(logs) == 0}

graph = StateGraph(AuditState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
