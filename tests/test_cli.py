import unittest

from hermes_control_pack.cli import parser


class CLITests(unittest.TestCase):
    def test_setup_defaults_to_balanced_and_continuity(self):
        args = parser().parse_args(["setup"])
        self.assertEqual(args.soul, "balanced")
        self.assertFalse(args.no_context_engine)
        self.assertFalse(args.project_context)

    def test_install_uses_packaged_assets_when_build_omitted(self):
        args = parser().parse_args(["install"])
        self.assertIsNone(args.build_dir)


if __name__ == "__main__":
    unittest.main()
