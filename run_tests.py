#!/usr/bin/env python3
"""
Test runner script for Gemini CLI SDK.
This script runs different test suites and provides a summary.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command: {e}")
        return False, "", str(e)

def main():
    """Main test runner."""
    print("Gemini CLI SDK Test Runner")
    print("=" * 60)
    
    # Set PYTHONPATH
    os.environ['PYTHONPATH'] = '.'
    
    test_suites = [
        {
            'cmd': 'python3 -m pytest tests/test_basic.py::TestGeminiConfig -v',
            'description': 'Configuration Tests'
        },
        {
            'cmd': 'python3 -m pytest tests/test_basic.py::TestConfigManager -v',
            'description': 'Config Manager Tests'
        },
        {
            'cmd': 'python3 -m pytest tests/test_basic.py::TestSessionManager -v',
            'description': 'Session Manager Tests'
        },
        {
            'cmd': 'python3 -m pytest tests/test_logging.py -v',
            'description': 'Logging Tests'
        },
        {
            'cmd': 'python3 -m pytest tests/test_system_commands.py -v',
            'description': 'System Commands Tests'
        },
        {
            'cmd': 'python3 -m pytest tests/test_real_interactions.py -v',
            'description': 'Real Interactions Tests'
        },
        {
            'cmd': 'python3 -m pytest tests/test_basic.py::TestGeminiClient::test_client_context_manager -v',
            'description': 'Fixed Async Test'
        }
    ]
    
    results = []
    
    for suite in test_suites:
        success, stdout, stderr = run_command(suite['cmd'], suite['description'])
        results.append({
            'name': suite['description'],
            'success': success,
            'stdout': stdout,
            'stderr': stderr
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{result['name']:<30} {status}")
        if result['success']:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All test suites passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test suite(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
