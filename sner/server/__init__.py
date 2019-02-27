"""main application package module"""

from flask import flash, Flask, render_template
from sner.server.commands import init_db, init_data
from sner.server.controller.scheduler import job, profile, task
from sner.server.extensions import db, toolbar


def create_app():
	"""flask application factory"""

	app = Flask(__name__)
	app.config.from_envvar('SNER_CONFIG')

	toolbar.init_app(app)
	db.init_app(app)

	app.register_blueprint(job.blueprint, url_prefix='/scheduler/job')
	app.register_blueprint(profile.blueprint, url_prefix='/scheduler/profile')
	app.register_blueprint(task.blueprint, url_prefix='/scheduler/task')

	app.cli.add_command(init_db)
	app.cli.add_command(init_data)

	@app.route('/')
	def index_route(): # pylint: disable=unused-variable
		flash('info', 'info')
		flash('success', 'success')
		flash('warning', 'warning')
		flash('error', 'error')
		return render_template('index.html')

	@app.template_filter('datetime')
	def format_datetime(value, fmt="%Y-%m-%dT%H:%M:%S"): # pylint: disable=unused-variable
		"""Format a datetime"""
		if value is None:
			return ""
		return value.strftime(fmt)

	return app
