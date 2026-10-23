#!/usr/bin/env python3
import sys
import os
import unittest
import importlib.util

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_runner_path = os.path.join(root_dir, "test_runner.py")

spec = importlib.util.spec_from_file_location("root_test_runner", root_runner_path)
root_test_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_test_runner)

class TestEdgeCaseRunner(unittest.TestCase):
    def test_runner_initialization(self):
        runner = root_test_runner.EdgeCaseTestRunner()
        self.assertIsNotNone(runner)

if __name__ == "__main__":
    root_test_runner.main()
