from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FrozenFruitState(TypedDict):
    batch_id: str
    temperature_logs: List[float]
    passed_qc: bool

def validate_cold_chain(state: FrozenFruitState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    print(f"Validating cold chain for batch {state['batch_id']} at {avg_temp}C")
    return {"passed_qc": avg_temp <= -18.0}

def process_shipment(state: FrozenFruitState):
    print(f"Processing shipment {state['batch_id']}: {'Accepted' if state['passed_qc'] else 'Rejected'}")
    return {"passed_qc": state['passed_qc']}

graph = StateGraph(FrozenFruitState)
graph.add_node("validate", validate_cold_chain)
graph.add_node("process", process_shipment)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph = graph.compile()
