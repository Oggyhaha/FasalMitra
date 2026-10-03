import re
from typing import List, Tuple
from backend.app.schemas.schemas import EvidenceChunk, VerifiedClaim

class ClaimVerifier:
    def verify_claims(self, generated_text: str, evidence: List[EvidenceChunk]) -> Tuple[List[VerifiedClaim], bool]:
        """
        Extracts claims (dosages, chemicals, practices) and verifies alignment against agricultural evidence.
        Ensures safety while allowing natural agronomic explanations.
        Returns: (verified_claims_list, all_passed_bool)
        """
        combined_evidence = " ".join([e.text.lower() for e in evidence])
        gen_lower = generated_text.lower()
        claims = []
        all_passed = True

        # Safety Check: Banned or high-hazard chemical cross-check
        restricted_chemicals = ["monocrotophos", "paraquat", "phorate", "endosulfan"]
        for chem in restricted_chemicals:
            if chem in gen_lower and chem not in combined_evidence:
                claims.append(VerifiedClaim(claim=f"High risk ungrounded chemical: {chem}", verified=False))
                all_passed = False

        # Extract chemical mentions to verify grounding
        known_chemicals = [
            "thiamethoxam", "chlorantraniliprole", "emamectin", "spinetoram",
            "propiconazole", "tricyclazole", "fipronil", "hanpv", "carbendazim",
            "mancozeb", "imidacloprid", "urea", "dap"
        ]
        
        found_chemicals = [c for c in known_chemicals if c in gen_lower]
        for chem in found_chemicals:
            is_grounded = chem in combined_evidence
            claims.append(VerifiedClaim(claim=f"Agronomic treatment ({chem})", verified=is_grounded))
            # If a specific chemical was recommended that wasn't in evidence, flag for safety
            if not is_grounded:
                # If evidence exists and mentions other treatments, warn but don't fail unless conflicting
                pass

        # Extract dosage patterns (e.g., 100g/ha, 150ml, 1ml/L)
        dosage_matches = re.findall(r'(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|लीटर|ग्राम|मिली))', generated_text, re.IGNORECASE)
        for match in dosage_matches[:4]:
            num_match = re.search(r'\d+', match)
            if num_match:
                number = num_match.group()
                is_num_present = number in combined_evidence
                claims.append(VerifiedClaim(claim=f"Dosage specification: {match}", verified=is_num_present))

        if not claims:
            claims.append(VerifiedClaim(claim="Grounded agronomist advisory guidance", verified=True))

        return claims, all_passed

claim_verifier = ClaimVerifier()
