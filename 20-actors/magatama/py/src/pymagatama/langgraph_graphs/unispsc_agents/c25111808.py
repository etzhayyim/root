from langgraph.graph import StateGraph, END
from typing import TypedDict

class YachtProcurementState(TypedDict):
    vessel_id: str
    compliance_passed: bool
    inspection_report: str

def validate_yacht_specs(state: YachtProcurementState):
    print(f"Validating yacht specifications for vessel {state['vessel_id']}")
    return {"compliance_passed": True}

def conduct_maritime_inspection(state: YachtProcurementState):
    print("Executing marine survey and inspection.")
    return {"inspection_report": "Survey Passed: Hull integrity confirmed."}

defgraph = StateGraph(YachtProcurementState)
defgraph.add_node("validate", validate_yacht_specs)
defgraph.add_node("inspect", conduct_maritime_inspection)
defgraph.set_entry_point("validate")
defgraph.add_edge("validate", "inspect")
defgraph.add_edge("inspect", END)
graph = defgraph.compile()
