from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from operator import add

class ProcessingState(TypedDict):
    data_input: dict
    processing_steps: Annotated[Sequence[str], add]
    is_validated: bool

def validate_data_integrity(state: ProcessingState):
    print(f"Validating data: {state['data_input']}")
    return {"is_validated": True, "processing_steps": ["validation_pass"]}

def execute_algorithm(state: ProcessingState):
    if not state.get("is_validated", False):
        return {"processing_steps": ["execution_skipped"]}
    print("Executing specialized algorithms.")
    return {"processing_steps": ["algorithm_executed"]}

def finalize_report(state: ProcessingState):
    print("Finalizing processing report.")
    return {"processing_steps": ["report_generated"]}

graph = StateGraph(ProcessingState)
graph.add_node("validate", validate_data_integrity)
graph.add_node("execute", execute_algorithm)
graph.add_node("report", finalize_report)

graph.set_entry_point("validate")
graph.add_edge("validate", "execute")
graph.add_edge("execute", "report")
graph.add_edge("report", END)

compiled_graph = graph.compile()
