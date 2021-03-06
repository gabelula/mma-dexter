from dexter.app import app

# setup assets
from flask.ext.assets import Environment, Bundle
assets = Environment(app)
assets.url_expire = False
assets.debug      = app.config['ENV'] == 'development'
assets.directory  = '%s/public' % app.config.root_path
assets.load_path  = ['assets']
assets.url        = '/public'

assets.register('css',
    Bundle(
      'css/bootstrap-3.0.3.min.css',
      'css/bootstrap-3.0.3-theme.min.css',
      'css/font-awesome-4.0.3.min.css',
      'css/chosen.min.css',
      'css/datepicker3.css',
      'css/bootstrap-datetimepicker.min.css',
      'css/daterangepicker-bs3.css',
      Bundle(
        'css/*.scss',
        filters='pyscss',
        output='css/app.%(version)s.css'),
      output='css/all.%(version)s.css'))

assets.register('admin-css',
    Bundle(
      'css/admin.css',
    ))


js = Bundle(
    'js/jquery-1.10.2.min.js',
    'js/bootstrap-3.0.3.min.js',
    'js/typeahead.bundle-0.10.1.min.js',
    'js/ujs.js',
    'js/chosen.jquery.min.js',
    'js/app.js',
    'js/document.js',
    'js/person.js',
    'js/moment.min.js',
    'js/bootstrap-datepicker.js',
    'js/bootstrap-datetimepicker.min.js',
    'js/daterangepicker-1.3.5.js',
    output='js/app.%(version)s.js')
assets.register('js', js)

assets.register('activity',
    Bundle(
        'js/highcharts-4.0.1.js',
        'js/underscore-1.6.0.js',
        'js/activity.js',
        output='js/activity.%(version)s.js'))

# Helper that is available in templates, and returns the
# urls to the named assets.
def assets_helper(*args, **kwargs):
    result = []
    for f in args:
        try:
            result.append(assets[f])
        except KeyError:
            result.append(f)

    bundle = Bundle(*result, **kwargs)
    urls = bundle.urls(env=assets)

    return urls


@app.context_processor
def webassets_processor():
    return dict(webassets=assets_helper)
