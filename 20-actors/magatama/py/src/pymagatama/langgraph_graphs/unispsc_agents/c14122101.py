from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ThermalPaperState(TypedDict):
    paper_width: float
    roll_diameter: float
    archival_required: bool
    validation_logs: List[str]
    approved: bool

def validate_specs(state: ThermalPaperState) -> dict:
    logs = []
    if state['paper_width'] <= 0:
        logs.append('Invalid width')
    if state['roll_diameter'] > 200:
        logs.append('Diameter exceeds feeder capacity')
    return {'validation_logs': logs, 'approved': len(logs) == 0}

def update_inventory(state: ThermalPaperState) -> dict:
    return {'validation_logs': state['validation_logs'] + ['Inventory updated']}

graph = StateGraph(ThermalPaperState)
graph.add_node('validate', validate_specs)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
compile_graph = graph.compile()
