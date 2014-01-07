from ckan.authz import Authorizer
from ckan.lib.base import c, model
from ckan.lib.navl.dictization_functions import validate, missing
from ckan.lib.navl.validators import ignore_missing, keep_extras, not_empty, \
    empty, ignore, if_empty_same_as, not_missing, ignore_empty, ignore_missing, \
    not_empty, empty, ignore, keep_extras, ignore_missing, not_empty, keep_extras, \
    default
from ckan.logic import get_action, check_access
from ckan.logic.converters import convert_to_extras, convert_from_extras, \
    date_to_db, date_to_form
from ckan.logic.schema import package_form_schema, default_tags_schema
from ckan.plugins import IConfigurer, IConfigurer, IDatasetForm, IDatasetForm, \
    IGenshiStreamFilter, IGenshiStreamFilter, IPackageController, IPackageController, \
    IRoutes, IRoutes, implements, SingletonPlugin, implements, SingletonPlugin
from logging import getLogger, getLogger
import ckan.logic as logic
import ckan.logic.schema as default_schema
import ckan.logic.validators as val
import ckanext.dgvat_por.controllers.data_gv_at as gv
import os
import stream_filters

try:
    import json
except ImportError:
    import simplejson as json


log = getLogger(__name__)


def configure_template_directory(config, relative_path):
    configure_served_directory(config, relative_path, 'extra_template_paths')

def configure_public_directory(config, relative_path):
    configure_served_directory(config, relative_path, 'extra_public_paths')

def configure_served_directory(config, relative_path, config_var):
    'Configure serving of public/template directories.'
    assert config_var in ('extra_template_paths', 'extra_public_paths')
    this_dir = os.path.dirname(__file__)
    absolute_path = os.path.join(this_dir, relative_path)
    if absolute_path not in config.get(config_var, ''):
        if config.get(config_var):
            config[config_var] += ',' + absolute_path
        else:
            config[config_var] = absolute_path
            
class DgvatForm(SingletonPlugin):
    implements(IRoutes)
    implements(IConfigurer)
    implements(IGenshiStreamFilter)
    implements(IDatasetForm)
    
    log.fatal("Enter: %s" % __name__)
    def package_form(self):
        return 'package/datagvat_organization_form.html'
    
    
    def before_map(self, map):
        
        # Helpers to reduce code clutter
        GET = dict(method=['GET'])
        OPTIONS = dict(method=['OPTIONS'])   
                
        map.connect('/error/{action}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatErrorController')
        map.connect('/error/{action}/{id}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatErrorController')        
        
        map.connect('/dataset/new', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='new')
        map.connect('/dataset/edit/{id}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='edit')
        map.connect('/dataset/{id}.{format}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='read')
        map.connect('/dataset/{id}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='read')
        map.connect('/dataset/{id}/resource/{resource_id}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='resource_read')
        map.connect('/dataset/{id}/resource/{resource_id}/embed', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='resource_embedded_dataviewer')
        map.connect('/dataset/editresources/{id}', controller='ckanext.dgvat_por.controllers.data_gv_at:DgvatPackageController', action='editresources')
        map.connect('/user/edit/{id:.*}', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='edit')
        #m.connect('/user/reset/{id:.*}', action='perform_reset')
        map.connect('/user/register', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='register')
        map.connect('/user/login', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='login')
        map.connect('/user/_logout', '/user/logout', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='logout')
        map.connect('/user/logged_in', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='logged_in')
        map.connect('/user/logged_out', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='logged_out')
        map.connect('/user/logged_out_redirect', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='logged_out_page')
        #map.connect('/user/reset', action='request_reset')
        #m.connect('/user/me', action='me')
        map.connect('/user/set_lang/{lang}', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='set_lang')
        #m.connect('/user/{id:.*}', action='read')
        map.connect('/user', controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='index')        
        
        map.connect('home', '/', controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='search')
        map.connect('about', '/about', controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='about')
        map.connect('terms', '/terms', controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='terms')
        map.connect('help', '/help', controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='help')
        map.connect('register_api', '/register_api', controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='register')
        map.connect('import', '/import', controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='importexcel')
            
    # CKAN API versioned.
        register_list = [
                'package',
                'dataset',
                'resource',
                'tag',
                'group',
                'related',
                'authorizationgroup',
                'revision',
                'licenses',
                'rating',
                'user',
                'activity'
                ]
        register_list_str = '|'.join(register_list)
    
        # /api ver 3 or none
        with SubMapper(map, controller='ckanext.dgvat_por.controllers.dgvat_api:DgvatApiController', path_prefix='/api{ver:/3|}', ver='/3') as m:
            m.connect('/action/{logic_function}', action='action')
    
        # /api ver 1, 2, 3 or none
        with SubMapper(map, controller='ckanext.dgvat_por.controllers.dgvat_api:DgvatApiController', path_prefix='/api{ver:/1|/2|/3|}', ver='/1') as m:
            m.connect('', action='get_api')
            m.connect('/search/{register}', action='search')
    
        # /api ver 1, 2 or none
        with SubMapper(map, controller='ckanext.dgvat_por.controllers.dgvat_api:DgvatApiController', path_prefix='/api{ver:/1|/2|}', ver='/1') as m:
            m.connect('/tag_counts', action='tag_counts')
            m.connect('/rest', action='index')
            m.connect('/qos/throughput/', action='throughput', conditions=GET)
    
        # /api/rest ver 1, 2 or none
        with SubMapper(map, controller='ckanext.dgvat_por.controllers.dgvat_api:DgvatApiController', path_prefix='/api{ver:/1|/2|}', ver='/1',
                       requirements=dict(register=register_list_str)) as m:
    
            m.connect('/rest/{register}', action='list', conditions=GET)
            m.connect('/rest/{register}/{id}', action='show', conditions=GET)
            m.connect('/rest/{register}/{id}/:subregister', action='list',
                conditions=GET)
            m.connect('/rest/{register}/{id}/:subregister/{id2}', action='show',
                conditions=GET)
    
        # /api/util ver 1, 2 or none
        with SubMapper(map, controller='ckanext.dgvat_por.controllers.dgvat_api:DgvatApiController', path_prefix='/api{ver:/1|/2|}', ver='/1') as m:
            m.connect('/util/user/autocomplete', action='user_autocomplete')
            m.connect('/util/is_slug_valid', action='is_slug_valid',
                      conditions=GET)
            m.connect('/util/dataset/autocomplete', action='dataset_autocomplete',
                      conditions=GET)
            m.connect('/util/tag/autocomplete', action='tag_autocomplete',
                      conditions=GET)
            m.connect('/util/resource/format_autocomplete',
                      action='format_autocomplete', conditions=GET)
            m.connect('/util/resource/format_icon',
                      action='format_icon', conditions=GET)
            m.connect('/util/authorizationgroup/autocomplete',
                      action='authorizationgroup_autocomplete')
            m.connect('/util/group/autocomplete', action='group_autocomplete')
            m.connect('/util/markdown', action='markdown')
            m.connect('/util/dataset/munge_name', action='munge_package_name')
            m.connect('/util/dataset/munge_title_to_name',
                      action='munge_title_to_package_name')
            m.connect('/util/tag/munge', action='munge_tag')
            m.connect('/util/status', action='status')
    
        ###########
        ## /END API
        ###########        
        
        #log.fatal("==================================> %s" % map)
        return map
    
    
    def after_map(self, map):
        #log.fatal("==================================> %s" % map)
        return map
    
    
    def update_config(self, config):
        log.debug("update_config")
        config['package_form'] = 'data_gv_at'
        configure_template_directory(config, 'templates')
        configure_public_directory(config, 'public')
        
        
    def filter(self, stream):

        from pylons import request, tmpl_context as c
        routes = request.environ.get('pylons.routes_dict')
        log.debug(routes)
        if routes and \
               routes.get('controller') == 'package' and \
               routes.get('action') == 'read' and c.pkg.id:

            # Add dataset id to the UI
            stream = stream_filters.package_id_filter(stream, c.pkg)
        return stream
    
    
    def setup_template_variables(self, context, data_dict):
        log.debug("setup_template_variables")

    def package_types(self):
        return ['dataset']
    
    def is_fallback(self):
        return True  

    def form_to_db_schema(self):
        log.fatal("Enter form to db!!!")
        
        schema = {
                  'title': [if_empty_same_as("name"), unicode],
                  'name': [not_empty, unicode, val.name_validator, val.package_name_validator],
                  'license_id': [not_empty, unicode],
                  'maintainer': [ignore_missing, unicode],
                  'schema_name': [ignore_missing, unicode, convert_to_extras],
                  'maintainer_link': [ignore_missing, unicode, convert_to_extras],
                  'schema_language': [ignore_missing, unicode,convert_to_extras],
                  'schema_characterset': [ignore_missing, unicode,convert_to_extras],
                  'date_released': [ignore_missing, unicode, convert_to_extras],
                  'begin_datetime': [ignore_missing, unicode, convert_to_extras],
                  'end_datetime': [ignore_missing, unicode, convert_to_extras],
                  'metadata_linkage': [ignore_missing, unicode, convert_to_extras],
                  'attribute_description': [ignore_missing, unicode, convert_to_extras],
                  'publisher': [ignore_missing, unicode, convert_to_extras],
                  'geographic_toponym': [ignore_missing, unicode, convert_to_extras],
                  'geographic_bbox': [ignore_missing, unicode, convert_to_extras],
                  'lineage_quality': [ignore_missing, unicode, convert_to_extras],
                  'en_title_and_desc': [ignore_missing, unicode, convert_to_extras],
                  'license_citation':[ignore_missing, unicode, convert_to_extras],
                  'metadata_identifier':[ignore_missing, unicode, convert_to_extras],
                  'metadata_modified':[ignore_missing, unicode, convert_to_extras],
                  'date_updated':[ignore_missing, unicode, convert_to_extras],
                  'publishing_date':[ignore_missing, unicode, convert_to_extras],
                  'publishing_state':[ignore_missing, unicode, convert_to_extras],
                  'url': [ignore_missing, unicode],
                  'resources': default_schema.default_resource_schema(),
                  'state': [val.ignore_not_admin, ignore_missing],
                  'log_message': [unicode, val.no_http],
                  '__extras': [ignore], 
                  'revision_id': [ignore],
                  'update_frequency': [ignore_missing, unicode, convert_to_extras],
                  'categorization': [ignore_missing, unicode, self.add_to_extras],
                  'notes': [ignore_missing, unicode],
                  'tag_string': [ignore_missing, val.tag_string_convert],
                  'groups': {
                             'id': [ignore_missing, unicode],
                             'capacity': [ignore_missing, unicode],
                             '__extras': [ignore],
                            },
                  }
        
        schema['resources'].update({
                    'language':[ignore_missing], 
                    'characterset':[ignore_missing]
                       })


        return schema
    
    def add_to_extras(self, key, data, errors, context):
        # get current number of extras
        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras
        #extras.append({'key': key[-1], 'value': data[key]})
        #log.fatal("add to extras: %s, %s" % (key, data[key]))
        #log.fatal("extra_number: %s" % extra_number)
        #data[('extras', extra_number, 'key')] = key[0]
        cats =""
        allCat=[]
        for cur in data[key]:
            if cur != '[' and cur!=']':
                cats += cur
        for cat_desc, id in c.categorization:
            if id in cats:
                allCat.append(id)      
        #log.fatal("added categorizations:id %s" % allCat)
        #log.fatal("cats, key: %s,%s" % (cats, data[key]))
        #log.fatal("is list: %s" % isinstance(data[key], list))
        #data[('extras', extra_number, 'value')] = allCat
        extras.append({'key': key[-1], 'value': allCat})



    def db_to_form_schema(self):
        log.debug("Enter db to form")
        #c.categorization = gv.categorization
        #c.update_frequency = gv.update_frequency
        schema = logic.schema.package_form_schema()
        schema.update({
            'schema_name': [convert_from_extras, ignore_missing, unicode],
            'schema_language': [convert_from_extras, ignore_missing, unicode],
            'maintainer_link': [convert_from_extras, ignore_missing, unicode],
            'date_released': [convert_from_extras, ignore_missing, unicode],
            'begin_datetime': [convert_from_extras, ignore_missing, unicode],
            'end_datetime': [convert_from_extras, ignore_missing, unicode],
            'metadata_linkage': [convert_from_extras, ignore_missing, unicode],
            'attribute_description': [convert_from_extras, ignore_missing, unicode],
            'publisher': [convert_from_extras, ignore_missing, unicode],
            'geographic_toponym': [convert_from_extras, ignore_missing, unicode],
            'geographic_bbox': [convert_from_extras, ignore_missing, unicode],
            'lineage_quality': [convert_from_extras, ignore_missing, unicode],
            'en_title_and_desc': [convert_from_extras, ignore_missing, unicode],
            'license_citation':[convert_from_extras, ignore_missing, unicode],
            'metadata_identifier':[convert_from_extras, ignore_missing, unicode],
            'metadata_modified':[convert_from_extras, ignore_missing, unicode],
            'date_updated':[convert_from_extras, ignore_missing, unicode],
            'resources': default_schema.default_resource_schema(),
            'categorization': [convert_from_extras, ignore_missing],
            'update_frequency': [convert_from_extras, ignore_missing],
            'publishing_date': [convert_from_extras, ignore_missing],
            'publishing_state': [convert_from_extras, ignore_missing],
            'extras': {
                'key': [],
                'value': [],
                '__extras': [keep_extras]
            },
            'tags': {
                '__extras': [keep_extras]
            },
            'mandate': [convert_from_extras, ignore_missing],
            'national_statistic': [convert_from_extras, ignore_missing],
            '__extras': [keep_extras],
        })

        schema['groups'].update({
            'name': [not_empty, unicode],
            'title': [ignore_missing],
            'capacity': [ignore_missing, unicode]
        })

        schema['resources'].update({
            'created': [ignore_missing],
            'position': [not_empty],
            'last_modified': [ignore_missing],
            'cache_last_updated': [ignore_missing],
            'webstore_last_updated': [ignore_missing],
            'language':[ignore_missing],
            'characterset':[ignore_missing]
        })
        
        return schema

    def read_template(self):
        return 'package/read.html'

    
    def check_data_dict(self, schema=None):
        return

    def new_template(self):
        return 'package/new.html'

    def comments_template(self):
        return 'package/comments.html'

    def search_template(self):
        return 'package/search.html'

    def read_template(self):
        return 'package/read.html'

    def history_template(self):
        return 'package/history.html'

    def package_form(self):
        return 'package/datagvat_organization_form.html'



class SubMapper(object):
    # FIXME this is only used due to a bug in routes 1.11
    # hopefully we can use map.submapper(...) in version 1.12
    """Partial mapper for use with_options"""
    def __init__(self, obj, **kwargs):
        self.kwargs = kwargs
        self.obj = obj

    def connect(self, *args, **kwargs):
        newkargs = {}
        newargs = args
        for key in self.kwargs:
            if key == 'path_prefix':
                if len(args) > 1:
                    newargs = (args[0], self.kwargs[key] + args[1])
                else:
                    newargs = (self.kwargs[key] + args[0],)
            elif key in kwargs:
                newkargs[key] = self.kwargs[key] + kwargs[key]
            else:
                newkargs[key] = self.kwargs[key]
        for key in kwargs:
            if key not in self.kwargs:
                newkargs[key] = kwargs[key]
        return self.obj.connect(*newargs, **newkargs)

    # Provided for those who prefer using the 'with' syntax in Python 2.5+
    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass       