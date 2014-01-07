# -*- coding: utf-8 -*- 


from autoneg.accept import negotiate 
from ckan.authz import Authorizer
from ckan.controllers.group import GroupController
from ckan.controllers.home import CACHE_PARAMETER, HomeController
from ckan.controllers.package import PackageController
from ckan.lib.base import *
from ckan.lib.helpers import Page, json, url_for, date_str_to_datetime, json
from ckan.lib.i18n import get_lang
from ckan.lib.navl.dictization_functions import DataError, unflatten, validate, \
    DataError, unflatten, validate
from ckan.lib.navl.validators import ignore_missing, not_empty, keep_extras, \
    default
from ckan.lib.package_saver import PackageSaver, ValidationException
from ckan.lib.plugins import lookup_package_plugin
from ckan.lib.search import SearchError
from ckan.logic import NotFound, NotAuthorized, ValidationError, NotFound, \
    NotAuthorized, ValidationError, NotFound, NotAuthorized, ValidationError, \
    get_action, check_access, tuplize_dict, clean_dict, parse_params, \
    flatten_to_string_key, get_action, check_access, tuplize_dict, clean_dict, \
    parse_params, flatten_to_string_key
from ckan.logic.converters import convert_to_extras, convert_from_extras, \
    date_to_db, date_to_form
from ckan.logic.schema import package_form_schema, default_tags_schema
from ckan.model.group import Group
from ckan.model.user import User
from ckan.plugins import IDatasetForm, IGroupForm, IConfigurer, \
    IPackageController, implements, SingletonPlugin
from datetime import datetime
from ckan.controllers.home import CACHE_PARAMETER
from pylons import config
from pylons.i18n import _
from urllib import urlencode, urlencode
import ckan.authz
import ckan.forms
import ckan.lib.plugins
import ckan.logic.action.get
import ckan.logic.schema as default_schema
import ckan.misc
import ckan.rating
import genshi
import logging







log = logging.getLogger(__name__)


update_frequency = [('', ''),
                    ('continual', 'kontinuierlich'),
                    ('daily', 'taeglich'),
                    ('weekly', 'woechentlich'),
                    ('fortnightly', '14-taegig'),
                    ('monthly', 'monatlich'),
                    ('quarterly', 'quartalsweise'),
                    ('biannually', 'halbjaehrlich'),
                    ('annually', 'jaehrlich'),
                    ('asNeeded', 'nach Bedarf'),
                    ('irregular', 'unregelmaessig'),
                    ('notPlanned', 'nicht geplant'),
                    ('unknown', 'unbekannt'),]

categorization = [
                  ('Arbeit', 'arbeit'),
                  (u'Bevölkerung', 'bevoelkerung'),
                  ('Bildung und Forschung', 'bildung-und-forschung'),
                  ('Finanzen und Rechnungswesen', 'finanzen-und-rechnungswesen'),
                  ('Geographie und Planung', 'geographie-und-planung'),
                  ('Gesellschaft und Soziales', 'gesellschaft-und-soziales'),
                  ('Gesundheit', 'gesundheit'),
                  ('Kunst und Kultur', 'kunst-und-kultur'),
                  ('Land und Forstwirtschaft', 'land-und-forstwirtschaft'),
                  ('Sport und Freizeit', 'sport-und-freizeit'),
                  ('Umwelt', 'umwelt'),
                  ('Verkehr und Technik', 'verkehr-und-technik'),
                  ('Verwaltung und Politik', 'verwaltung-und-politik'),
                  ('Wirtschaft und Tourismus', 'wirtschaft-und-tourismus'),]


class DgvatPackageController(PackageController):
    implements(IPackageController)
    
    package_form = 'package/datagvat_organization_form.html'
    log.fatal("Enter: DgvatPackageController")

    def __before__(self, action, **params):
        log.fatal("Before: %s" % __name__)
        BaseController.__before__(self, action, **params)
        context = ''
        self._setup_local_variables()
        
    def _setup_local_variables(self):
        c.update_frequency = update_frequency
        c.categorization = categorization
        log.fatal('setup template variables in DgvatPackageController as user: %s' % c.user)
        if c.userobj:
            c.is_sysadmin = Authorizer().is_sysadmin(c.user)
            usergroups = c.userobj.get_groups()
        else:
            c.is_sysadmin = False
            usergroups = ''
        
        if len(usergroups) == 1 and not c.is_sysadmin:
            c.show_cdo_features = True
            c.cdo_group = usergroups[0]
            log.fatal(c.cdo_group)
        else:
            c.show_cdo_features = False
            #removed
    
    def _setup_template_variables(self, context, data_dict=None, package_type=None):
        log.debug("_setup_template_variables")
        c.update_frequency = update_frequency
        c.categorization = categorization
        c.groups_authz = get_action('group_list_authz')(context, data_dict)
        data_dict.update({'available_only':True})
        #c.groups_available = get_action('group_list_authz')(context, data_dict)
        c.groups_available = c.userobj and c.userobj.get_groups('organization') or []
        c.licences = [('', '')] + model.Package.get_license_options()
        c.is_sysadmin = Authorizer().is_sysadmin(c.user)
        if c.is_sysadmin:
            c.groups_available = Group.all('organization') 
        log.fatal("is_sysadmin: %s" % c.is_sysadmin)
        log.fatal("groups: %s" % c.groups_available)

        ## This is messy as auths take domain object not data_dict
        context_pkg = context.get('package',None)
        pkg = context_pkg or c.pkg
        if pkg:
            try:
                if not context_pkg:
                    context['package'] = pkg
                check_access('package_change_state',context)
                c.auth_for_change_state = True
            except NotAuthorized:
                c.auth_for_change_state = False

    def _form_save_redirect(self, pkgname, action):
        if action in ('new'):
            url = h.url_for(controller='package', action='edit', id=pkgname)
            redirect(url)
        
        elif action in ('edit'):
            url = request.params.get('return_to') or \
                config.get('package_%s_return_url' % action)
            if url:
                url = url.replace('<NAME>', pkgname)
            else:
                url = h.url_for(controller='package', action='read', id=pkgname)
            redirect(url)
            
    def edit(self, id, data=None, errors=None, error_summary=None):
        package_type = self._get_package_type(id)
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'extras_as_string': True,
                   'save': 'save' in request.params,
                   'moderated': config.get('moderated'),
                   'pending': True,}

        if context['save'] and not data:
            return self._save_edit(id, context)
        try:
            c.pkg_dict = get_action('package_show')(context, {'id':id})
            context['for_edit'] = True
            old_data = get_action('package_show')(context, {'id':id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            data = data or old_data
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound:
            abort(404, _('Dataset not found'))

        c.pkg = context.get("package")
        c.resources_json = json.dumps(data.get('resources',[]))

        try:
            check_access('package_update',context)
        except NotAuthorized, e:
            abort(401, _('User %r not authorized to edit %s') % (c.user, id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.errors_json = json.dumps(errors)

        self._setup_template_variables(context, {'id': id}, package_type=package_type)
        c.related_count = len(c.pkg.related)

        # TODO: This check is to maintain backwards compatibility with the old way of creating
        # custom forms. This behaviour is now deprecated.
        if hasattr(self, 'package_form'):
            c.form = render(self.package_form, extra_vars=vars)
        else:
            c.form = render(self._package_form(package_type=package_type), extra_vars=vars)
        log.fatal(self._package_form(package_type=package_type))
        log.fatal("form: %s" % c.form)
        if (c.action == u'editresources'):
          return render('package/editresources.html')
        else:
          return render('package/edit.html')            

    def editresources(self, id, data=None, errors=None, error_summary=None):
        '''Hook method made available for routing purposes.'''
        return self.edit(id,data,errors,error_summary)

    def new(self, data=None, errors=None, error_summary=None):
        package_type = self._guess_package_type(True)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'extras_as_string': True,
                   'save': 'save' in request.params,}

        # Package needs to have a organization group in the call to check_access
        # and also to save it
        try:
            check_access('package_create',context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a package'))
                
        if context['save'] and not data:
            return self._save_new(context)

        data = data or clean_dict(unflatten(tuplize_dict(parse_params(
            request.params, ignore_keys=[CACHE_PARAMETER]))))
        c.resources_json = json.dumps(data.get('resources',[]))

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.errors_json = json.dumps(errors)

        self._setup_template_variables(context, {'id': id})

        # TODO: This check is to maintain backwards compatibility with the old way of creating
        # custom forms. This behaviour is now deprecated.
        if hasattr(self, 'package_form'):
            c.form = render(self.package_form, extra_vars=vars)
        else:
            c.form = render(self._package_form(package_type=package_type), extra_vars=vars)
        return render( self._new_template(package_type))

    def _save_new(self, context, package_type=None):
        from ckan.lib.search import SearchIndexError
        try:
            data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.POST))))
            data_dict['type'] = package_type
            context['message'] = data_dict.get('log_message', '')
            pkg = get_action('package_create')(context, data_dict)
            data_dict['id'] = pkg['id']       
            data_dict['metadata_identifier']  = pkg['id']
            data_dict['metadata_modified'] = pkg['metadata_created']
            get_action('package_update')(context, data_dict)
            
            self._form_save_redirect(pkg['name'], 'new')
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound, e:
            abort(404, _('Dataset not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except SearchIndexError, e:
            abort(500, _(u'Unable to add package to search index.') + repr(e.args))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)
        
    def read(self, id, format='html'):
        if not format == 'html':
            ctype, extension, loader = \
                self._content_type_from_extension(format)
            if not ctype:
                # An unknown format, we'll carry on in case it is a
                # revision specifier and re-constitute the original id
                id = "%s.%s" % (id, format)
                ctype, format, loader = "text/html; charset=utf-8", "html", \
                    MarkupTemplate
        else:
            ctype, format, loader = "text/html; charset=utf-8", "html", \
                    MarkupTemplate
            
        self._setup_local_variables()

        response.headers['Content-Type'] = ctype

        package_type = self._get_package_type(id.split('@')[0])
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'extras_as_string': True,
                   'for_view': True}
        data_dict = {'id': id}

        # interpret @<revision_id> or @<date> suffix
        split = id.split('@')
        if len(split) == 2:
            data_dict['id'], revision_ref = split
            if model.is_id(revision_ref):
                context['revision_id'] = revision_ref
            else:
                try:
                    date = date_str_to_datetime(revision_ref)
                    context['revision_date'] = date
                except TypeError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
                except ValueError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
        elif len(split) > 2:
            abort(400, _('Invalid revision format: %r') % 'Too many "@" symbols')

        #check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
            c.resources_json = json.dumps(c.pkg_dict.get('resources',[]))
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)

        # used by disqus plugin
        c.current_package_id = c.pkg.id
        c.related_count = len(c.pkg.related)

        # Add the package's activity stream (already rendered to HTML) to the
        # template context for the package/read.html template to retrieve
        # later.
        c.package_activity_stream = \
                ckan.logic.action.get.package_activity_list_html(context,
                    {'id': c.current_package_id})

        PackageSaver().render_package(c.pkg_dict, context)

        template = self._read_template( package_type )
        template = template[:template.index('.')+1] + format

        return render( template, loader_class=loader)
        
    def _save_edit(self, name_or_id, context):
        from ckan.lib.search import SearchIndexError
        try:
            data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.POST))))
            context['message'] = data_dict.get('log_message', '')
            if not context['moderated']:
                context['pending'] = False
            data_dict['id'] = name_or_id
            data_dict['metadata_modified'] = datetime.utcnow()
            log.fatal(data_dict)
            pkg = get_action('package_update')(context, data_dict)
            #get_action('package_update')(context, data_dict)
            if request.params.get('save', '') == 'Approve':
                get_action('make_latest_pending_package_active')(context, data_dict)
            c.pkg = context['package']
            c.pkg_dict = pkg

            self._form_save_redirect(pkg['name'], 'edit')
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)
        except NotFound, e:
            abort(404, _('Dataset not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except SearchIndexError, e:
            abort(500, _(u'Unable to update search index.') + repr(e.args))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(name_or_id, data_dict, errors, error_summary)
    
        