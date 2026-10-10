#!/usr/bin/env python3
"""
FasalMitra Comprehensive Edge-Case Test Runner
Executes structured test cases from JSON, evaluates multi-lingual NLP,
safety gates, target extraction, and outputs a complete summary to a text file.
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Reconfigure stdout to UTF-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.core.query_understanding import query_understanding_engine
from backend.app.core.safety_gate import pre_safety_gate
from backend.app.core.retrieval_engine import retrieval_engine
from backend.app.db.database import SessionLocal

DEFAULT_TEST_FILE = os.path.join(os.path.dirname(__file__), "tests", "edge_test_cases.json")
DEFAULT_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "test_summary.txt")


class EdgeCaseTestRunner:
    def __init__(self, test_file_path: str = DEFAULT_TEST_FILE, output_file_path: str = DEFAULT_OUTPUT_FILE):
        self.test_file_path = test_file_path
        self.output_file_path = output_file_path
        self.db = SessionLocal()
        self.results: List[Dict[str, Any]] = []

    def load_test_cases(self) -> List[Dict[str, Any]]:
        """Loads test cases from specified JSON file."""
        if not os.path.exists(self.test_file_path):
            alt = os.path.join(os.path.dirname(__file__), "tests", os.path.basename(self.test_file_path))
            if os.path.exists(alt):
                self.test_file_path = alt
            elif os.path.exists(os.path.join(os.path.dirname(__file__), self.test_file_path)):
                self.test_file_path = os.path.join(os.path.dirname(__file__), self.test_file_path)
            else:
                raise FileNotFoundError(f"Test cases JSON file not found at: {self.test_file_path}")
        
        with open(self.test_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Support both a list of test cases or a wrapped dict {"test_cases": [...]}
        if isinstance(data, dict):
            return data.get("test_cases", data.get("TEST_CASES", []))
        return data

    def run_single_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Runs validation for a single edge test case."""
        t_id = test.get("id", "UNKNOWN")
        category = test.get("category", "GENERAL")
        query = test.get("query", "")
        lang = test.get("language", "en")
        exp_intent = test.get("expected_intent")
        exp_target = test.get("expected_target")
        must_not_contain = test.get("must_not_contain_targets", [])

        start_time = time.perf_counter()

        # 1. Query Understanding Evaluation with Conversation Context
        requires_ctx = test.get("requires_conversation_context", False)
        if requires_ctx:
            nlp = query_understanding_engine.parse_query(query, conversation_context=getattr(self, "conv_ctx", {}))
        else:
            nlp = query_understanding_engine.parse_query(query)
            self.conv_ctx = {}

        detected_target = nlp.get("target")
        detected_intent = nlp.get("intent")
        detected_crop = nlp.get("crop")

        if not hasattr(self, "conv_ctx"):
            self.conv_ctx = {}
        if detected_target:
            self.conv_ctx["last_target"] = detected_target
        if detected_crop:
            self.conv_ctx["last_crop"] = detected_crop

        # 2. Safety Gate Evaluation
        safe_pass, risk_lvl, safe_reason = pre_safety_gate.evaluate(query, nlp, {"crop": detected_crop})

        # 3. Knowledge Retrieval Evaluation
        retrieved_evidence = []
        try:
            retrieved_evidence = retrieval_engine.retrieve(self.db, query, detected_crop, "General", top_k=2)
        except Exception:
            pass

        duration_ms = (time.perf_counter() - start_time) * 1000

        test_type = test.get("test_type", "")

        # Evaluation Rules:
        passed = True
        reasons = []

        # 1. Pure Out-of-Domain / Safety Refusal cases (no specific target or intent expected)
        if (not exp_target and not exp_intent) or category in ["OUT_OF_DOMAIN_UNSAFE", "SAFETY_BANNED_TOXIC"] or t_id.startswith("X_OOD") or "OOD" in t_id:
            is_refused = (not safe_pass) or (detected_intent in ["MARKET", "SCHEMES", "GENERAL_CROP"]) or (detected_target is None)
            if not is_refused:
                passed = False
                reasons.append(f"Expected safe refusal/OOD detection, but got safe_pass={safe_pass}")

        # 2. Target Alignment (if expected_target is specified)
        if exp_target:
            target_matched = (detected_target == exp_target)
            if not target_matched:
                # Check if target appears in top retrieved evidence title/text
                top_text = " ".join([e.title.lower() + " " + e.text.lower() for e in retrieved_evidence])
                if exp_target.lower().replace("_", " ") in top_text or exp_target.lower() in top_text:
                    target_matched = True

            if not target_matched:
                passed = False
                reasons.append(f"Target mismatch: expected '{exp_target}', got '{detected_target}'")

        # 3. Intent Alignment (if expected_intent is specified)
        if exp_intent and passed:
            intent_matched = (detected_intent == exp_intent)
            if not intent_matched:
                synonyms = {
                    "PLANT_PROTECTION": ["PEST_DISEASE", "MANAGEMENT_CONTROL", "DIAGNOSIS_SYMPTOMS", "DISEASE_CAUSE", "GENERAL_CROP", "INPUT_USAGE"],
                    "MANAGEMENT_CONTROL": ["INPUT_USAGE", "PEST_DISEASE", "PLANT_PROTECTION", "GENERAL_CROP"],
                    "DIAGNOSIS_SYMPTOMS": ["PEST_DISEASE", "PLANT_PROTECTION", "DISEASE_CAUSE"],
                    "DISEASE_CAUSE": ["PEST_DISEASE", "PLANT_PROTECTION", "DIAGNOSIS_SYMPTOMS"],
                    "GENERAL_CROP": ["PEST_DISEASE", "MANAGEMENT_CONTROL", "INPUT_USAGE", "PLANT_PROTECTION", "DIAGNOSIS_SYMPTOMS"]
                }
                if detected_intent in synonyms.get(exp_intent, []):
                    intent_matched = True

            if not intent_matched:
                passed = False
                reasons.append(f"Intent mismatch: expected '{exp_intent}', got '{detected_intent}'")

        # 4. Check Negative Targets (must_not_contain_targets)
        for forbidden in must_not_contain:
            forb_lower = forbidden.lower()
            if detected_target and forb_lower in detected_target.lower():
                passed = False
                reasons.append(f"Negation violation: found forbidden target '{forbidden}' in detected target")

        status = "PASS" if passed else "FAIL"

        return {
            "id": t_id,
            "category": category,
            "query": query,
            "language": lang,
            "expected_intent": exp_intent,
            "detected_intent": detected_intent,
            "expected_target": exp_target,
            "detected_target": detected_target,
            "detected_crop": detected_crop,
            "safety_passed": safe_pass,
            "safety_reason": safe_reason,
            "retrieved_count": len(retrieved_evidence),
            "status": status,
            "reasons": reasons,
            "duration_ms": duration_ms
        }

    def run_all(self, category_filter: str = None) -> Dict[str, Any]:
        """Runs the entire test suite and records all metrics."""
        test_cases = self.load_test_cases()
        
        if category_filter:
            test_cases = [t for t in test_cases if t.get("category") == category_filter or category_filter in t.get("id", "")]

        print(f"\n================================================================================")
        print(f"  FASALMITRA AUTOMATED ADVISORY TEST RUNNER")
        print(f"  Loaded {len(test_cases)} test cases from: {os.path.basename(self.test_file_path)}")
        print(f"================================================================================\n")

        self.results = []
        start_suite = time.perf_counter()

        for idx, tc in enumerate(test_cases, 1):
            res = self.run_single_test(tc)
            self.results.append(res)
            
            icon = "✅ PASS" if res["status"] == "PASS" else "❌ FAIL"
            exp_str = f"Exp: [{res['expected_target'] or res['expected_intent'] or 'N/A'}]"
            act_str = f"Act: [{res['detected_target'] or res['detected_intent']}]"
            
            # Print clean progress line
            clean_query = res['query'][:45] + "..." if len(res['query']) > 45 else res['query']
            print(f"[{idx:02d}/{len(test_cases):02d}] {res['id']:<14} {icon}  {res['duration_ms']:5.1f}ms  | {clean_query:<48} | {exp_str} -> {act_str}")

        total_duration = time.perf_counter() - start_suite
        metrics = self._compute_metrics(total_duration)
        self._write_summary_file(metrics)

        print(f"\n--------------------------------------------------------------------------------")
        print(f"  TEST SUITE COMPLETED in {total_duration:.2f}s")
        print(f"  Pass Rate: {metrics['pass_rate']:.1f}% ({metrics['passed_count']}/{metrics['total_count']} passed)")
        print(f"  Summary Report Saved: {self.output_file_path}")
        print(f"--------------------------------------------------------------------------------\n")

        return metrics

    def _compute_metrics(self, total_duration: float) -> Dict[str, Any]:
        """Calculates aggregated metrics per suite and per category."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0

        latencies = [r["duration_ms"] for r in self.results]
        avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        min_latency = min(latencies) if latencies else 0.0

        # Category breakdown
        categories: Dict[str, Dict[str, int]] = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "failed": 0}
            categories[cat]["total"] += 1
            if r["status"] == "PASS":
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": total,
            "passed_count": passed,
            "failed_count": failed,
            "pass_rate": pass_rate,
            "total_duration_sec": total_duration,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
            "categories": categories
        }

    def _write_summary_file(self, metrics: Dict[str, Any]):
        """Formats and writes a comprehensive summary text file."""
        lines = []
        lines.append("==========================================================================================")
        lines.append("                  FASALMITRA ADVISORY ENGINE - AUTOMATED TEST SUITE REPORT                ")
        lines.append("==========================================================================================")
        lines.append(f"Report Generated  : {metrics['timestamp']}")
        lines.append(f"Test Cases File   : {os.path.abspath(self.test_file_path)}")
        lines.append(f"Summary Output    : {os.path.abspath(self.output_file_path)}")
        lines.append(f"Execution Duration: {metrics['total_duration_sec']:.2f} seconds")
        lines.append("------------------------------------------------------------------------------------------\n")

        lines.append("------------------------------------------------------------------------------------------")
        lines.append("                                   1. EXECUTIVE SUMMARY                                   ")
        lines.append("------------------------------------------------------------------------------------------")
        lines.append(f"  • Total Test Cases Evaluated : {metrics['total_count']}")
        lines.append(f"  • Successfully Passed        : {metrics['passed_count']} ({metrics['pass_rate']:.1f}%)")
        lines.append(f"  • Failed / Mismatched        : {metrics['failed_count']}")
        lines.append(f"  • Average Latency per Query  : {metrics['avg_latency_ms']:.2f} ms")
        lines.append(f"  • Min / Max Latency Range    : {metrics['min_latency_ms']:.2f} ms / {metrics['max_latency_ms']:.2f} ms\n")

        lines.append("------------------------------------------------------------------------------------------")
        lines.append("                              2. CATEGORY BREAKDOWN TABLE                                 ")
        lines.append("------------------------------------------------------------------------------------------")
        lines.append(f"{'Category Name':<34} | {'Total':<6} | {'Passed':<6} | {'Failed':<6} | {'Pass Rate':<10}")
        lines.append("-" * 75)
        for cat_name, stats in metrics["categories"].items():
            cat_rate = (stats["passed"] / stats["total"] * 100.0) if stats["total"] > 0 else 0.0
            lines.append(f"{cat_name:<34} | {stats['total']:<6} | {stats['passed']:<6} | {stats['failed']:<6} | {cat_rate:6.1f}%")
        lines.append("-" * 75 + "\n")

        lines.append("------------------------------------------------------------------------------------------")
        lines.append("                               3. DETAILED TEST CASE AUDIT LOG                             ")
        lines.append("------------------------------------------------------------------------------------------")
        lines.append(f"{'ID':<13} | {'Status':<6} | {'Time(ms)':<8} | {'Query Snippet':<40} | {'Expected Target/Intent':<24} | {'Actual Target/Intent'}")
        lines.append("-" * 120)

        for r in self.results:
            exp_val = str(r["expected_target"] or r["expected_intent"] or "N/A")
            act_val = str(r["detected_target"] or r["detected_intent"] or "N/A")
            q_snip = r["query"][:37] + "..." if len(r["query"]) > 37 else r["query"]
            lines.append(f"{r['id']:<13} | {r['status']:<6} | {r['duration_ms']:7.1f} | {q_snip:<40} | {exp_val:<24} | {act_val}")

        lines.append("-" * 120 + "\n")

        # Section 4: Failures Diagnostic
        failed_tests = [r for r in self.results if r["status"] == "FAIL"]
        lines.append("------------------------------------------------------------------------------------------")
        lines.append(f"                          4. DIAGNOSTIC & FAILURE ANALYSIS ({len(failed_tests)} Cases)                         ")
        lines.append("------------------------------------------------------------------------------------------")
        if not failed_tests:
            lines.append("  All test cases passed successfully! Zero regressions or mismatches detected.\n")
        else:
            for ft in failed_tests:
                lines.append(f"\n[FAILED TEST CASE: {ft['id']}]")
                lines.append(f"  • Category        : {ft['category']}")
                lines.append(f"  • Query           : \"{ft['query']}\"")
                lines.append(f"  • Language        : {ft['language']}")
                lines.append(f"  • Expected Target : {ft['expected_target']}")
                lines.append(f"  • Detected Target : {ft['detected_target']}")
                lines.append(f"  • Expected Intent : {ft['expected_intent']}")
                lines.append(f"  • Detected Intent : {ft['detected_intent']}")
                lines.append(f"  • Detected Crop   : {ft['detected_crop']}")
                lines.append(f"  • Failure Reasons : {', '.join(ft['reasons'])}")

        lines.append("\n==========================================================================================")
        lines.append("                                    END OF TEST REPORT                                    ")
        lines.append("==========================================================================================")

        with open(self.output_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="FasalMitra Advisory Edge-Case Test Runner")
    parser.add_argument("--test-file", "-f", default=DEFAULT_TEST_FILE, help="Path to input JSON test cases file")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_FILE, help="Path to output summary text file")
    parser.add_argument("--category", "-c", default=None, help="Filter by specific category")

    args = parser.parse_args()

    runner = EdgeCaseTestRunner(test_file_path=args.test_file, output_file_path=args.output)
    metrics = runner.run_all(category_filter=args.category)

    # Return exit code based on failures
    sys.exit(0 if metrics["failed_count"] == 0 else 1)


if __name__ == "__main__":
    main()
