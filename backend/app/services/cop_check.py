from typing import Tuple, Optional

# Simple map: IBAN -> expected name (simulated CoP)
EXPECTED = {
    "RO49AAAA1B31007593840000": "John Doe Investments SRL",
}

async def confirmation_of_payee(dst_iban: str, provided_name: Optional[str]) -> Tuple[bool, str]:
    expected = EXPECTED.get(dst_iban)
    if not expected:
        return True, "No data"
    if not provided_name:
        return False, f"Expected '{expected}', but no name provided"
    ok = provided_name.strip().lower() == expected.lower()
    return ok, ("Match" if ok else f"Mismatch vs '{expected}'")
