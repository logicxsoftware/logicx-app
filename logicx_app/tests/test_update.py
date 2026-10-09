from pathlib import Path
from unittest.mock import call, patch

import frappe
from frappe.tests import IntegrationTestCase

from logicx_app import update


class TestLiveUpdate(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_status_requires_administrator(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			update.get_update_status(refresh=0)

	def test_run_update_uses_fixed_command_sequence(self):
		repository = Path("/workspace/logicx-app")
		bench = Path("/bench")
		with (
			patch.object(update, "_repository_root", return_value=repository),
			patch.object(update, "_bench_root", return_value=bench),
			patch.object(update, "_run", return_value="") as run,
			patch.object(update, "_write_state") as write_state,
			patch.object(update, "_read_version", return_value="0.1.1"),
		):
			update.run_update("logicx.localhost")

		self.assertEqual(
			run.call_args_list,
			[
				call(
					["git", "-c", "safe.directory=/workspace/logicx-app", "pull", "--ff-only"],
					repository,
					180,
				),
				call(["bench", "--site", "logicx.localhost", "migrate"], bench, 900),
				call(["bench", "build", "--app", "logicx_app"], bench, 1200),
				call(["bench", "--site", "logicx.localhost", "clear-cache"], bench, 180),
			],
		)
		self.assertEqual(write_state.call_args_list[-1].args[0]["phase"], "complete")
