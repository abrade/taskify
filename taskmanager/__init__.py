from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.views.tasks')
    config.include('.views.teams')
    config.include('.views.workers')
    config.include('.views.scripts')
    config.scan()
    return config.make_wsgi_app()
