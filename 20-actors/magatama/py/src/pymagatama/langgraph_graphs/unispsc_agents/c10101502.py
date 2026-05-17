from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CattleIngestState(TypedDict):
    cattle_ids: List[str]
    health_status: List[str]
    validation_errors: Annotated[List[str], operator.add]
    is_cleared: bool

def validate_health_docs(state: CattleIngestState):
    # Simulate health doc check logic
    validated = [s for s in state['health_status'] if 'certified' in s]
    errors = [s for s in state['health_status'] if 'certified' not in s]
    return {'validation_errors': errors, 'is_cleared': len(errors) == 0}

def quarantine_workflow(state: CattleIngestState):
    # Simulate quarantine processing
    print(f"Processing quarantine for: {state['cattle_ids']}")
    return {'is_cleared': state['is_cleared']}

graph = StateGraph(CattleIngestState)
graph.add_node("validate_health", validate_health_docs)
graph.add_node("quarantine", quarantine_workflow)
graph.set_entry_point("validate_health")
graph.add_edge("validate_health", "quarantine")
graph.add_edge("quarantine", END)
graph = graph.compile()