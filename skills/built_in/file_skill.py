from system.file_controller import FileController


class FileSkill:

    name = "file_action"

    def run(self, params):

        action = params.get("action")

        if action == "create_file":
            return FileController.create_file(params.get("path"))

        elif action == "delete_file":
            return FileController.delete_file(params.get("path"))

        elif action == "move_file":
            return FileController.move_file(
                params.get("path"),
                params.get("destination")
            )

        elif action == "list_files":
            return FileController.list_files(params.get("path"))

        return "error"