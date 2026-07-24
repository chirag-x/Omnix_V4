import unittest
from unittest.mock import patch

from system.app_controller import AppController


class FakeProcess:

    def __init__(self, pid, name, exe=None):
        self.pid = pid
        self.info = {
            "name": name,
            "exe": exe or name,
        }
        self.terminated = False
        self.killed = False

    def name(self):
        return self.info["name"]

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class AppControllerTests(unittest.TestCase):

    def test_process_aliases_cover_display_names(self):
        self.assertIn(
            "code.exe",
            AppController._process_names_for(
                "Visual Studio Code",
                AppController._canonical_name("Visual Studio Code"),
            ),
        )
        self.assertIn(
            "winword.exe",
            AppController._process_names_for(
                "Microsoft Word",
                AppController._canonical_name("Microsoft Word"),
            ),
        )

    @patch("system.app_controller.psutil.wait_procs")
    @patch("system.app_controller.psutil.process_iter")
    def test_close_app_terminates_all_matching_processes(
        self,
        process_iter,
        wait_procs,
    ):
        spotify_main = FakeProcess(10, "Spotify.exe")
        spotify_helper = FakeProcess(11, "Spotify.exe")
        chrome = FakeProcess(12, "chrome.exe")

        process_iter.side_effect = [
            [spotify_main, spotify_helper, chrome],
            [],
        ]
        wait_procs.return_value = ([spotify_main, spotify_helper], [])

        result = AppController.close_app("spotify")

        self.assertEqual("success", result)
        self.assertTrue(spotify_main.terminated)
        self.assertTrue(spotify_helper.terminated)
        self.assertFalse(chrome.terminated)

    @patch("system.app_controller.psutil.process_iter", return_value=[])
    def test_close_app_reports_missing_process(self, _process_iter):
        self.assertEqual("error", AppController.close_app("spotify"))


if __name__ == "__main__":
    unittest.main()
