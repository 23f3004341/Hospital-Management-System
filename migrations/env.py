import logging
from logging.config import fileConfig
from flask import current_app
from alembic import context

# Alembic Config Setup
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Get Engine Helper (for Flask-SQLAlchemy v2 & v3)
def get_engine():
    try:
        # for Flask-SQLAlchemy < 3
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # for Flask-SQLAlchemy >= 3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

# Metadata Configuration
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


# Migration Runners
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        render_as_batch=True  # important for SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    # properly define conf_args for Flask-Migrate
    conf_args = current_app.extensions['migrate'].configure_args
    conf_args.setdefault("process_revision_directives", process_revision_directives)
    conf_args.setdefault("render_as_batch", True)  # needed for SQLite

    connectable = get_engine()

    with connectable.connect() as connection:
        conf_args.pop("compare_type", None)  # prevent duplicate argument error
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()

# Entry Point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
