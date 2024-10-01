from flask import Blueprint

main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

# Import views at the bottom to avoid circular imports
from views import *
