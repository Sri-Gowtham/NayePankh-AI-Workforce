"""
tests/test_e2e_flow.py — E2E integration test
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.db_tools import create_session
from agents.supervisor import SupervisorAgent

def test_e2e_flow():
    # 1. Create a session
    sess_res = create_session("default", "supervisor")
    if not sess_res.get("success"):
        print("FAIL: create_session failed:", sess_res.get("error"))
        return False
    session_id = sess_res["data"]["session_id"]
    print("PASS: Session created successfully:", session_id)
    
    # 2. Instantiate Supervisor
    try:
        supervisor = SupervisorAgent()
        print("PASS: SupervisorAgent instantiated successfully.")
    except Exception as e:
        print("FAIL: SupervisorAgent instantiation failed:", e)
        return False
        
    # 3. Test Routing & Agent response for Volunteer
    print("\nTesting: General Greeting...")
    res = supervisor.run("hello, who are you and how does this operating system work?", session_id)
    if not res or "error" in res.lower() or "ollama" in res.lower() or "{" in res:
        print("FAIL: Greeting response is invalid:", res)
        return False
    print("PASS: Greeting responded with natural language:\n", res)
    
    # 4. Test Internship Query
    print("\nTesting: Internship Query...")
    res = supervisor.run("How do I apply for an internship at NayePankh?", session_id)
    if not res or "error" in res.lower() or "ollama" in res.lower() or "{" in res:
        print("FAIL: Internship response is invalid:", res)
        return False
    print("PASS: Internship responded with natural language:\n", res)

    # 5. Test Analytics KPI Generation
    print("\nTesting: KPI analytics tool call...")
    res = supervisor.run("Generate the monthly KPI impact report for the NGO", session_id)
    if not res or "error" in res.lower() or "ollama" in res.lower() or "{" in res:
        print("FAIL: KPI analytics response is invalid:", res)
        return False
    print("PASS: KPI responded with natural language:\n", res)

    # 6. Test Internship Registration Tool call with exact query
    print("\nTesting: Internship Registration (add intern named Ram with email ram@gmail.com)...")
    res = supervisor.run("add intern named Ram with email ram@gmail.com", session_id)
    if not res or "error" in res.lower() or "ollama" in res.lower() or "{" in res or "tool_use_failed" in res.lower():
        print("FAIL: Internship registration response is invalid:", res)
        return False
    print("PASS: Internship registration responded successfully:\n", res)

    print("\nALL E2E STABILITY TESTS PASSED.")
    return True

if __name__ == "__main__":
    test_e2e_flow()
