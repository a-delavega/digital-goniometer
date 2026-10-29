import unittest
from unittest.mock import patch
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the main module (not just a specific class) to test the CLI flow
import main

class TestCLI(unittest.TestCase):
    
    @patch('main.GoniometerApp.run')
    @patch('builtins.input', side_effect=['1', 'A', 'X'])
    def test_cli_invalid_input_fallback(self, mock_input, mock_run):
        """Test that the CLI handles invalid string inputs by using defaults without crashing."""
        crashed = False
        try:
            main.main([])
        except Exception:
            crashed = True
            
        self.assertFalse(crashed, "The CLI wizard crashed when given invalid string inputs.")
        mock_run.assert_called_once()

    @patch('main.GoniometerApp.run')
    def test_cli_explicit_arguments_bypass_wizard(self, mock_run):
        """Test that explicit CLI flags configure joints without prompting user input."""
        with patch('main.GoniometerApp.__init__', return_value=None) as mock_app_init:
            main.main(['--joints', 'INDEX_PIP', 'THUMB_IP', '--camera', '1', '--no-export'])
            
            mock_app_init.assert_called_once()
            _, kwargs = mock_app_init.call_args
            target_joints = kwargs.get('target_joints', [])
            self.assertEqual(len(target_joints), 2)
            self.assertEqual(target_joints[0].name, 'INDEX_PIP')
            self.assertEqual(target_joints[1].name, 'THUMB_IP')
            self.assertEqual(kwargs.get('camera_index'), 1)
            self.assertFalse(kwargs.get('export_session'))
            mock_run.assert_called_once()

    @patch('main.GoniometerApp.run')
    @patch('builtins.input', side_effect=['1', '2', '2'])
    def test_cli_invalid_argument_falls_back_to_wizard(self, mock_input, mock_run):
        """Test that passing completely invalid joint names falls back to the interactive wizard."""
        with patch('main.GoniometerApp.__init__', return_value=None) as mock_app_init:
            main.main(['--joints', 'NON_EXISTENT_JOINT'])
            mock_input.assert_called()
            mock_app_init.assert_called_once()
            mock_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
