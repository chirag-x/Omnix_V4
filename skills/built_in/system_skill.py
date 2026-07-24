from system.app_controller import AppController


class SystemSkill:

    name = "open_app"

    def run(self, params):

        app = params.get("app")

        if not app:
            return "error"

        return AppController.open_app(app)