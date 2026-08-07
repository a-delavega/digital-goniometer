import unittest
from unittest.mock import patch
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the main module (not just a specific class) to test the CLI flow
import main

class TestCLI(unittest.TestCase):
    
    # We use decorators to inject our Mocks into the test.
    # 1. We mock GoniometerApp.run so the webcam DOES NOT turn on during the test.
    # 2. We mock builtins.input to simulate a user typing '1' (one joint), 
    #    and then typing invalid letters 'A' and 'X' instead of the expected menu numbers.
    @patch('main.GoniometerApp.run')
    @patch('builtins.input', side_effect=['1', 'A', 'X'])
    def test_cli_invalid_input_fallback(self, mock_input, mock_run):
        """Test that the CLI handles invalid string inputs by using defaults without crashing."""
        
        crashed = False
        try:
            # Execute the main function which triggers the CLI wizard
            main.main()
        except Exception:
            crashed = True
            
        # Assertions
        # 1. The program should not crash (it should catch the 'A' and 'X' and apply defaults)
        self.assertFalse(crashed, "The CLI wizard crashed when given invalid string inputs.")
        
        # 2. It should successfully reach the end of the wizard and attempt to start the app
        mock_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()