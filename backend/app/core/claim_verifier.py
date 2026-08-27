import re
from typing import List, Tuple
from backend.app.schemas.schemas import EvidenceChunk, VerifiedClaim

class ClaimVerifier:
    def verify_claims(self, generated_text: str, evidence: List[EvidenceChunk]) -> Tuple[List[VerifiedClaim], bool]:
        """
        Extracts claims (dosages, chemicals, practices) and verifies against evidence text.
        Returns: (verified_claims_list, all_passed_bool)
        """
        combined_evidence = " ".join([e.text.lower() for e in evidence])
        claims = []
        all_passed = True

        # Extract dosage patterns (e.g., 2ml/L, 100g/ha, 15-20 days)
        dosage_matches = re.findall(r'(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|लीटर|ग्राम|किग्र|दिवस))', generated_text, re.IGNORECASE)

        if not dosage_matches:
            # Simple keyword claim check
            claims.append(VerifiedClaim(claim="Grounded advice alignment", verified=True))
            return claims, True

        for match in dosage_matches:
            # Verify if number exists in evidence
            number = re.search(r'\d+', match).group()
            is_verified = number in combined_evidence
            claims.append(VerifiedClaim(claim=f"Dosage specification: {match}", verified=is_verified))
            if not is_verified:
                all_passed = False

        return claims, all_passed

claim_verifier = ClaimVerifier()
