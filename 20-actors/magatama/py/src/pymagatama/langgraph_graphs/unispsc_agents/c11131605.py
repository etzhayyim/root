from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class MineralProcessState(TypedDict):
    purity_metrics: List[float]
    safety_check_passed: bool
    process_steps: Annotated[List[str], operator.add]

def validate_purity(state: MineralProcessState):
    avg_purity = sum(state['purity_metrics']) / len(state['purity_metrics']) if state['purity_metrics'] else 0
    return {'safety_check_passed': avg_purity >= 0.99}

def execute_refinement(state: MineralProcessState):
    return {'process_steps': ['Catalyst Injection', 'Temperature Stabilization', 'Fractional Separation']}

graph = StateGraph(MineralProcessState)
graph.add_node('validate', validate_purity)
graph.add_node('refine', execute_refinement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'refine')
graph.add_edge('refine', END)
graph = graph.compile()