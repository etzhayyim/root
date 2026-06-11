from typing import TypedDict, List
from src.domain.entities import Opportunity
from src.adapters.repository import CRMRepository

class CloseOpportunityState(TypedDict):
    input_data: dict
    opportunity: Opportunity | None
    errors: List[str]
    status: str

def parse_request(state: CloseOpportunityState) -> dict:
    return {"status": "PARSED"}

def fetch_opportunity(state: CloseOpportunityState) -> dict:
    repo = CRMRepository()
    opp_id = state["input_data"].get("opportunity_id", "")
    opp = repo.get_opportunity(opp_id)
    
    errors = state.get("errors", [])
    if not opp:
        errors.append("Opportunity not found.")
        
    return {"opportunity": opp, "errors": errors}

def check_opp_exists(state: CloseOpportunityState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "update_stage"

def update_stage(state: CloseOpportunityState) -> dict:
    opp: Opportunity = state["opportunity"]
    stage = state["input_data"].get("stage_name", "Closed Won")
    
    opp.StageName = stage
    if stage == "Closed Won":
        opp.Probability = 100.0
    elif stage == "Closed Lost":
        opp.Probability = 0.0
        
    return {"opportunity": opp}

def validate_opp(state: CloseOpportunityState) -> dict:
    opp: Opportunity = state["opportunity"]
    errors = state.get("errors", [])
    
    if not opp.validate_won():
        errors.append("Validation Failed: Won opportunity must have Amount > 0 and 100% Probability.")
        
    return {"errors": errors}

def check_validation(state: CloseOpportunityState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "save"

def save_opp(state: CloseOpportunityState) -> dict:
    opp: Opportunity = state["opportunity"]
    repo = CRMRepository()
    repo.save_opportunity(opp) # Automatically publishes event if Closed Won
    
    return {"status": "SUCCESS"}

def reject_opp(state: CloseOpportunityState) -> dict:
    return {"status": "REJECTED"}
