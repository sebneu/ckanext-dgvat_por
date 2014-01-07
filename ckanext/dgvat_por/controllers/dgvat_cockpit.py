# -*- coding: utf-8 -*- 


from ckan.authz import Authorizer
from ckan.controllers.group import GroupController
from ckan.controllers.home import HomeController
from ckan.controllers.package import PackageController
from ckan.lib.base import *
from ckan.lib.helpers import Page, url_for
from ckan.lib.navl.validators import ignore_missing, not_empty, keep_extras, \
    default
from ckan.lib.plugins import lookup_package_plugin
from ckan.lib.search import SearchError
from ckan.logic import NotFound, NotAuthorized, ValidationError, get_action, \
    check_access
from ckan.logic.converters import convert_to_extras, convert_from_extras, \
    date_to_db, date_to_form
from ckan.logic.schema import package_form_schema, default_tags_schema
from ckan.model.user import User
from urllib import urlencode
import ckan.lib.mailer as mailer
import ckan.model as model
import genshi
import logging
import shutil
from ckan.lib.helpers import Page,pager_url
from ckan.lib.plugins import lookup_group_plugin



log = logging.getLogger(__name__)

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def map_organization(org):
    if org  == 'bka':
        return 'REMOVED'
    else:
        return ''

def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v)) \
                                  for k, v in params]

def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)

def search_url(params):
    url = h.url_for(controller='ckanext.dgvat_por.controllers.dgvat_cockpit:DgvatCockpitController', action='search')
    return url_with_params(url, params)

autoneg_cfg = [
    ("application", "xhtml+xml", ["html"]),
    ("text", "html", ["html"]),
    ("application", "rdf+xml", ["rdf"]),
    ("application", "turtle", ["ttl"]),
    ("text", "plain", ["nt"]),
    ("text", "x-graphviz", ["dot"]),
    ]

class DgvatCockpitController(PackageController):
    log.debug("Enter: %s" % __name__)
    
    def __before__(self, action, **params):
        log.fatal("Before: %s" % c.user)
        context = ''
        self._setup_template_variables(context)
        super(DgvatCockpitController, self).__before__(action)
        if not c.user:
            log.fatal("No User in PackageController")    
            h.redirect_to(controller='user', action='login')   
            
    def _groupform_to_db_schema(self, group_type=None):
        return lookup_group_plugin(group_type).form_to_db_schema()
    
    def _get_group_type(self, id):
        """
        Given the id of a group it determines the type of a group given
        a valid id/name for the group.
        """
        group = model.Group.get( id )
        if not group:
            return None

        return group.type        
    
    def _search_template(self, package_type):
        return 'home/index.html'    
    
    def _setup_template_variables(self, context):
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
            #REMOVED
            
        log.fatal("%s/%s/%s" % (c.is_sysadmin, c.show_cdo_features, c.cdo_group))  
            
    def search(self):
        from ckan.lib.search import SearchError

        package_type = self._guess_package_type()
            
        #log.fatal('administered: %s' % c.userobj.number_administered_packages())
        #log.fatal('edited: %s' % c.userobj.number_of_edits())            

        try:
            context = {'model':model,'user': c.user or c.author}
            check_access('site_read',context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))
            
        self._setup_template_variables(context)
            
        q = c.q = request.params.get('q', u'') # unicode format (decoded from utf8)
        c.query_error = False
        try:
            page = int(request.params.get('page', 1))
        except ValueError, e:
            abort(400, ('"page" parameter must be an integer'))
        limit = g.datasets_per_page

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k,v in request.params.items() if k != 'page']
        
        if c.show_cdo_features:
            if request.params.get('groups') == None:
                params_nopage.append(('groups', c.cdo_group.name))
            c.rss_url = "/katalog/group/history/%s?format=atom" % c.cdo_group.name
            c.rssnew_url = "/katalog/group/history/%s?format=atom&created=1" % c.cdo_group.name
            c.api_url = "/katalog/api/rest/group/%s" % c.cdo_group.name
            
            
        def drill_down_url(alternative_url=None, **by):
            params = set(params_nopage)
            params |= set(by.items())
            if alternative_url:
                return url_with_params(alternative_url, params)
            return search_url(params)

        c.drill_down_url = drill_down_url

        def remove_field(key, value):
            params = list(params_nopage)
            params.remove((key, value))
            return search_url(params)

        c.remove_field = remove_field

        sort_by = request.params.get('sort', None)
        #Sort data by metadata descending
        sort_by = 'metadata_modified desc'
        params_nosort = [(k, v) for k,v in params_nopage if k != 'sort']
        def _sort_by(fields):
            """
            Sort by the given list of fields.

            Each entry in the list is a 2-tuple: (fieldname, sort_order)

            eg - [('metadata_modified', 'desc'), ('name', 'asc')]

            If fields is empty, then the default ordering is used.
            """
            params = params_nosort[:]

            if fields:
                sort_string = ', '.join( '%s %s' % f for f in fields )
                params.append(('sort', sort_string))
            return search_url(params)
        c.sort_by = _sort_by
        if sort_by is None:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [ field.split()[0] for field in sort_by.split(',') ]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        c.search_url_params = urlencode(_encode_params(params_nopage))

        try:
            c.fields = []
            search_extras = {}
            fq = ''
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s:"%s"' % (param, value)
                    else:
                        search_extras[param] = value
            if c.show_cdo_features:
                if request.params.get('groups') == None:            
                    c.fields.append(('groups', c.cdo_group.name))
                    fq += ' %s:"%s"' % ('groups', c.cdo_group.name)    

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'for_view': True}

            data_dict = {
                'q':q,
                'fq':fq,
                'facet.field':g.facets,
                'rows':limit,
                'start':(page-1)*limit,
                'sort': sort_by,
                'extras':search_extras
            }

            query = get_action('package_search')(context,data_dict)

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )
            results = query['results']
            #for pack in results:
                #publishing_state_found = False
                #if pack.state == 'prepared':
                #for item in pack.get('extras'):
                #    if item.get('key') == 'publishing_state':
                #        publishing_state_found = True
                #        pack['publishing_state'] = item.get('value').replace('"', '')
                #if not publishing_state_found:
                #    pack['publishing_state'] = 'active'  
            c.facets = query['facets']
            c.search_facets = query['search_facets']
            c.page.items = results 
        except SearchError, se:
            log.error('Dataset search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.page = h.Page(collection=[])
            
        return render( self._search_template(package_type))


    def about(self):
        context = {'model':model,'user': c.user or c.author}
        self._setup_template_variables(context)
        return render('home/about.html')
    
    def help(self):
        context = {'model':model,'user': c.user or c.author}
        self._setup_template_variables(context)
        return render('home/help.html')
    
    def terms(self):
        context = {'model':model,'user': c.user or c.author}
        self._setup_template_variables(context)
        return render('home/terms.html')
    
    def register(self):
        context = {'model':model,'user': c.user or c.author}
        self._setup_template_variables(context)
        
        log.debug("group: %s" % request.params.get('organization'))
        log.debug("name: %s" % request.params.get('name'))
        log.debug("phone: %s" % request.params.get('phone'))
        log.debug("email: %s" % request.params.get('email'))
        log.debug("api: %s" % request.params.get('api'))
        log.debug("sent: %s" % request.params.get('sent'))
        log.debug("comment: %s" % request.params.get('comment'))
        if request.params.get('sent'):
            c.sent = request.params.get('sent')
            msg = ""
            msg += u"%s meldet eine api für %s unter: %s!\r\n" % (request.params.get('name'), request.params.get('organization'), request.params.get('api'))
            msg += u"Kontakt unter: %s und %s\r\n" % (request.params.get('phone'), request.params.get('email'))
            msg += u"Anmerkungen: %s" % request.params.get('comments')
            mailer.mail_recipient('data','data@brz.gv.at','API Request',msg)
        else:
            c.sent = 0
        return render('home/register_api.html')
    
    def importexcel(self):
        user = model.User.get('admin')
        context = {'model':model,'user': user,'session':model.Session}
        log.fatal(c.user)
        
        self._setup_template_variables(context)
        group = c.cdo_group
        groupharvester_id = 0
        con = {'model': model, 'session': model.Session,
               'user': c.user or c.author,
               'schema': self._groupform_to_db_schema(group.type),
               'for_view': True}
        data_dict = {'id': group.id}

        try:
            c.group_dict = get_action('group_show')(con, data_dict)
            c.group = con['group']
            for e in c.group_dict['extras']:
                if e['key'] == u'harvester':
                    groupharvester_id = e['value']
                    pass
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)        
        ##insert code to handle different groups
        #group = 'stadt-wien'
        groupharvester_id = groupharvester_id.replace('\"', '')
        if groupharvester_id == 0:
            abort(404,_('Harvester not properly configured'))
        
        if request.params.get('sent'):
            c.sent = request.params.get('sent')
            tempfile = request.POST['file']
            filepath = '/importFiles/'+ group.name + '/'
            ensure_dir(filepath)
            filepath = filepath + '/import.xls'
            perm_file = open(filepath, 'wb');
            shutil.copyfileobj(tempfile.file, perm_file)
            with open(filepath, "r") as myfile:
                os.chmod(filepath, 0777)
            #context = {'model':model, 'user':c.user or c.author, 'session':model.Session}
            try:
                get_action('harvest_job_create')(context,{'source_id':groupharvester_id})
            except Exception:
                pass
            h.flash_success(_(u'Der Import wurde angestossen und wird innerhalb der nächsten 15 Minuten erledigt'))
        else:
            c.sent = 0
        try:
            c.source = get_action('harvest_source_show')(context, {'id':groupharvester_id})

            c.page = Page(
                collection=c.source['status']['packages'],
                page=request.params.get('page', 1),
                items_per_page=20,
                url=pager_url
            )
        except NotFound:
            abort(404,_('Harvest source not found'))
        return render('home/import.html')        