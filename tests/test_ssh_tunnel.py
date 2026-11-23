import subprocess
import unittest
from unittest.mock import Mock, patch

import ghost


class TunnelLifecycleTests(unittest.TestCase):
    def run_session(self, state='device', error=None):
        process = Mock()
        process.poll.return_value = None
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if command[0] == '/test/scrcpy' and error:
                raise error
            if command[-1] == 'get-state':
                return subprocess.CompletedProcess(command, 0, state, '')
            return subprocess.CompletedProcess(command, 0, '', '')

        with patch.object(ghost.shutil, 'which', side_effect=lambda name: '/test/' + name), \
             patch.object(ghost, 'choose_stream_settings', return_value=['--no-audio']), \
             patch.object(ghost, 'ssh_connection_settings', return_value=['/test/ssh', '--', 'phone']), \
             patch('builtins.input', return_value='5555'), \
             patch('builtins.print'), \
             patch.object(ghost, 'wait_ssh_tunnel'), \
             patch.object(ghost.subprocess, 'Popen', return_value=process) as popen, \
             patch.object(ghost.subprocess, 'run', side_effect=run):
            try:
                ghost.control_via_ssh()
            except KeyboardInterrupt:
                if not isinstance(error, KeyboardInterrupt):
                    raise
        return process, popen.call_args.args[0], calls

    def test_tunnel_is_local_and_cleans_up_after_scrcpy(self):
        process, command, calls = self.run_session()
        forward = command[command.index('-L') + 1]
        self.assertTrue(forward.startswith('127.0.0.1:'))
        self.assertTrue(forward.endswith(':127.0.0.1:5555'))
        self.assertIn('ExitOnForwardFailure=yes', command)
        self.assertIn('ControlPersist=no', command)
        scrcpy = next(call for call in calls if call[0] == '/test/scrcpy')
        serial = scrcpy[scrcpy.index('--serial') + 1]
        self.assertIn('--force-adb-forward', scrcpy)
        self.assertEqual(calls[-1], ['/test/adb', 'disconnect', serial])
        process.terminate.assert_called_once()
        process.wait.assert_called_once()

    def test_failed_adb_never_launches_scrcpy_and_stops_tunnel(self):
        process, _, calls = self.run_session(state='unauthorized')
        self.assertFalse(any(call[0] == '/test/scrcpy' for call in calls))
        self.assertEqual(calls[-1][1], 'disconnect')
        process.terminate.assert_called_once()

    def test_scrcpy_start_failure_cleans_up(self):
        process, _, calls = self.run_session(error=OSError('launch failed'))
        self.assertEqual(calls[-1][1], 'disconnect')
        process.terminate.assert_called_once()

    def test_interrupt_cleans_up(self):
        process, _, calls = self.run_session(error=KeyboardInterrupt())
        self.assertEqual(calls[-1][1], 'disconnect')
        process.terminate.assert_called_once()

    def test_ssh_failure_is_detected_before_adb(self):
        process = Mock()
        process.poll.return_value = 255
        with self.assertRaises(RuntimeError), patch.object(ghost.subprocess, 'run') as run:
            ghost.wait_ssh_tunnel(process, '/test/ssh', '/missing/control', 'phone')
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
