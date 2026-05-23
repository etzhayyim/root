from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrigamiState(TypedDict):
    paper_specs: dict
    validation_log: list

def validate_material(state: OrigamiState):
    specs = state['paper_specs']
    logs = []
    if specs.get('gsm', 0) < 60 or specs.get('gsm', 0) > 100:
        logs.append('Warning: GSM outside optimal folding range')
    return {'validation_log': logs}

def finalize_procurement(state: OrigamiState):
    return {'validation_log': state['validation_log'] + ['Procurement specification verified']}

graph = StateGraph(OrigamiState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
