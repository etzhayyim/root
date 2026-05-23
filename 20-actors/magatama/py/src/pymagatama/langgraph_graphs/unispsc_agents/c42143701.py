from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhototherapyState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_air_specs(state: PhototherapyState):
    specs = state['spec_data']
    valid = 'hepa' in specs.get('filtration', '').lower() and specs.get('airflow_m3h', 0) > 0
    return {'is_compliant': valid}

def filter_check(state: PhototherapyState):
    return 'validate'

graph = StateGraph(PhototherapyState)
graph.add_node('validate', validate_air_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
