# -*- coding: utf-8 -*- 

import logging
from pylons import session, g

import genshi
from urllib import quote

import ckan.misc
from ckan.lib.base import *
from ckan.lib import mailer
from ckan.authz import Authorizer
from ckan.lib.navl.dictization_functions import DataError, unflatten
from ckan.logic import NotFound, NotAuthorized, ValidationError 
from ckan.logic import check_access, get_action
from ckan.logic import tuplize_dict, clean_dict, parse_params
from ckan.logic.schema import user_new_form_schema, user_edit_form_schema
from ckan.logic.action.get import user_activity_list_html
from ckan.lib.captcha import check_recaptcha, CaptchaError
from ckan.controllers.user import UserController
import ckanext.dgvat_por.lib.dgvat_helper as dgvathelper
from ckan.lib.plugins import lookup_group_plugin
import ckan.logic.schema as schema
import ckan.lib.dictization.model_save as model_save


log = logging.getLogger(__name__)


class DgvatUserController(UserController):
    log.fatal("Enter: %s" % __name__)
    
    def _groupform_to_db_schema(self, group_type=None):
        return lookup_group_plugin(group_type).form_to_db_schema()    
    
    def __before__(self, action, **env):
        log.fatal("Before: %s" % __name__)
        UserController.__before__(self, action, **env)
        context = ''
        self._setup_template_variables(context)

 
    def _setup_template_variables(self, context):
        log.fatal('setup template variables in DgvatUserController as user: %s' % c.user)
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
            c.cdo_group = {'name': 'name', 'title':'title', 'image_url': ''}    
     
    def index(self):
        LIMIT = 20

        page = int(request.params.get('page', 1))
        c.q  = request.params.get('q', '')
        c.order_by = request.params.get('order_by', 'name')

        context = {'model': model,
                   'user': c.user or c.author,
                   'return_query': True}

        data_dict = {'q':c.q,
                     'order_by':c.order_by}
        try:
            check_access('user_list',context, data_dict)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        users_list = get_action('user_list')(context,data_dict)

        c.page = h.Page(
            collection=users_list,
            page=page,
            url=h.pager_url,
            item_count=users_list.count(),
            items_per_page=LIMIT
        )
        return render('user/list.html')
    
    def logout(self):
        log.fatal("logout user")
        # save our language in the session so we don't lose it
        session['lang'] = request.environ.get('CKAN_LANG')
        session.save()
        h.redirect_to(self._get_repoze_handler('logout_handler_path'))

    def set_lang(self, lang):
        # this allows us to set the lang in session.  Used for logging
        # in/out to prevent being lost when repoze.who redirects things
        session['lang'] = str(lang)
        session.save()

    def logged_out(self):
        log.fatal("logged out")
        # we need to get our language info back and the show the correct page
        lang = session.get('lang')
        c.user = None
        session.delete()
        h.redirect_to(locale=lang, controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='logged_out_page')    
    
    def logged_out_page(self):
        log.fatal("logged_out_page")
        context = ''
        self._setup_template_variables(context)
        return h.redirect_to(controller='ckanext.dgvat_por.controllers.dgvat_user:DgvatUserController', action='login')
    
    def login(self):
        lang = session.pop('lang', None)
        if lang:
            session.save()
            return h.redirect_to(locale=str(lang), controller='user', action='login')
        if 'error' in request.params:
            h.flash_error(request.params['error'])

        g.openid_enabled = False
        
        if not c.user:
            #removed                    

            if c.removed and not c.is_allowed_to_switch:
                #removed        
        
                try:
                    found = False
                    results = get_action('group_list')(context, data_dict)
                    #removed               
                except NotFound:
                    abort(404, _('Group not found'))
                except NotAuthorized:
                    abort(401, _('Unauthorized to read group %s') % id)              
            
                if not found:
                    msg = ""
                    if c.fullname:
                        msg += u"Name: %s\r\n" % c.fullname
                    if c.email:
                        msg += u"Email: %s\r\n" % c.email
                else:
                    #removed                
                    msg = ""
                    if c.fullname:
                        msg += u"Name: %s\r\n" % c.fullname
                    if c.email:
                        msg += u"Email: %s\r\n" % c.email
                    h.redirect_to(locale=lang, controller='user', action='logged_in')

            return render('user/login.html')
        else:
            h.redirect_to(controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='search')
    

    def logged_in(self):
        # we need to set the language via a redirect
        lang = session.pop('lang', None)
        session.save()
        if c.user:
            context = {'model': model,
                       'user': c.user}

            data_dict = {'id':c.user}

            user_dict = get_action('user_show')(context,data_dict)

            #h.flash_success(_("%s is now logged in") % user_dict['display_name'])
            h.redirect_to(controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='search')
        else:
            err = _('Login failed. Bad username or password.')
            h.flash_error(err)
            h.redirect_to(locale=lang, controller='user', action='login')


    
    
    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   }
        self._setup_template_variables(context)
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id}

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = validate(old_data, schema)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % '')
        except NotFound, e:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (ckan.authz.Authorizer().is_sysadmin(unicode(c.user)) or c.user == user_obj.name):
            abort(401, _('User %s not authorized to edit %s') % (str(c.user), id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        self._setup_template_variables(context)

        c.is_myself = True
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')

    def _save_new(self, context):
        try:
            data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            check_recaptcha(request)
            #removed
            user = get_action('user_create')(context, data_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.new(data_dict)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)
        if not c.user:
            # Redirect to a URL picked up by repoze.who which performs the login
            login_url = self._get_repoze_handler('login_handler_path')
            h.redirect_to('%s?login=%s&password=%s' % (
                login_url,
                str(data_dict['name']),
                quote(data_dict['password1'].encode('utf-8'))))
        else:
            # #1799 User has managed to register whilst logged in - warn user
            # they are not re-logged in as new user.
            h.flash_success(_('User "%s" is now registered but you are still logged in as "%s" from before') % (data_dict['name'], c.user))
            return render('user/logout_first.html')

    
    def register(self, data=None, errors=None, error_summary=None):
        return self.new(data, errors, error_summary)
    
    def new(self, data=None, errors=None, error_summary=None):
        '''GET to display a form for registering a new user.
           or POST the form data to actually do the user registration.
        '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._new_form_to_db_schema(),
                   'save': 'save' in request.params}
        self._setup_template_variables(context)
        log.fatal("new user - user %s is sysadmin: %s" % (c.user, c.is_sysadmin))
        
        try:
            check_access('user_create',context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a user'))
        
        if not c.is_sysadmin:
            abort(401, _('Unauthorized to create a user'))
            

        if context['save'] and not data:
            return self._save_new(context)

        #if c.user and not data:
            # #1799 Don't offer the registration form if already logged in
            #return render('user/logout_first.html')

        data = data or {}
        data['name'] =  request.params.get('user')
        data['password'] = ''  #removed
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        c.form = render(self.new_user_form, extra_vars=vars)
        return render('user/new.html')
    
    