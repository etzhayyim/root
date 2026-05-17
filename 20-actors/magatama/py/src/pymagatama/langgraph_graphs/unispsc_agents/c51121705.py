from typing import TypedDict
from langgraph.graph import StateGraph, END

class FelodipineState(TypedDict):
    batch_number: str
    purity_level: float
    storage_temp: float
    is_compliant: bool

def validate_quality(state: FelodipineState):
    compliant = state['purity_level'] >= 99.0 and state['storage_temp'] <= 25.0
    return {"is_compliant": compliant}

def process_logistics(state: FelodipineState):
    print(f"Processing batch {state['batch_number']} for pharmaceutical distribution.")
    return {}

graph = StateGraph(FelodipineState)
graph.add_node("validate", validate_quality)
graph.add_node("logistics", process_logistics)
graph.add_edge("validate", "logistics")
graph.add_edge("logistics", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()