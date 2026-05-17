from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralProcessState(TypedDict):
    ore_batch_id: str
    assay_results: dict
    compliance_score: float
    processing_steps: Annotated[List[str], add_messages]

def validate_ore_grade(state: MineralProcessState):
    grade = state['assay_results'].get('ore_grade_percentage', 0)
    return {'compliance_score': 1.0 if grade > 45.0 else 0.0}

def execute_refinement_workflow(state: MineralProcessState):
    return {'processing_steps': ['crushing', 'flotation', 'leaching']}

def build_mineral_graph():
    workflow = StateGraph(MineralProcessState)
    workflow.add_node('validate', validate_ore_grade)
    workflow.add_node('refine', execute_refinement_workflow)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', 'refine')
    workflow.add_edge('refine', END)
    return workflow.compile()

graph = build_mineral_graph()