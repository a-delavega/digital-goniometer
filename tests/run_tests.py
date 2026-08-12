import unittest
import sys

def main():
    """
    Test Runner for the Digital Goniometer project.
    Discovers and runs all unit tests in the 'tests' directory.
    """
    print("========================================")
    print("   RUNNING ALL GONIOMETER UNIT TESTS    ")
    print("========================================\n")
    
    # Automatically discover all test_*.py files in the 'tests' directory
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='tests', pattern='test_*.py')
    
    # Run the test suite with a detail level of 2 (verbosity=2)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return a success (0) or failure (1) exit code to the operating system
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed. The system is stable.")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == '__main__':
    main()