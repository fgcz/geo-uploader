from flask_admin import Admin, AdminIndexView
from flask_admin.menu import MenuLink
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

migrate = Migrate()

mail = Mail()

cache = Cache()

login_manager = LoginManager()
login_manager.login_view = "auth.login"


class HomeView(AdminIndexView):
    def is_visible(self):
        return False


# Config default flask-admin view
admin = Admin(
    name="Flask-Starter Admin",
    template_mode="bootstrap3",
    index_view=HomeView(name="Home"),
)

admin.add_link(
    MenuLink(
        name="Back to Dashboard",
        url="/dashboard",
        icon_type="glyph",
        icon_value="glyphicon-circle-arrow-left",
    )
)

admin.add_link(
    MenuLink(
        name="Logout", url="/logout", icon_type="glyph", icon_value="glyphicon-log-out"
    )
)
