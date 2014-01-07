import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request, tmpl_context as c
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from ckan.lib.base import BaseController
from ckan.lib.base import render
from ckan.controllers.error import ErrorController

import logging

log = logging.getLogger(__name__)

class DgvatErrorController(ErrorController):
    log.fatal(__name__)

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    def document(self):
        self._setup_template_variables()
        """Render the error document"""
        original_request = request.environ.get('pylons.original_request')
        original_response = request.environ.get('pylons.original_response')
        # When a request (e.g. from a web-bot) is direct, not a redirect
        # from a page. #1176
        if not original_response:
            return 'There is no error.'
        # Bypass error template for API operations.
        if original_request and original_request.path.startswith('/api'):
            return original_response.body
        # Otherwise, decorate original response with error template.
        log.fatal("error-response: %s" % literal(original_response.unicode_body))
        log.fatal("cgi-escape: %s" % cgi.escape(request.GET.get('message', '')))
        c.content = literal(original_response.unicode_body) or cgi.escape(request.GET.get('message', ''))
        c.prefix=request.environ.get('SCRIPT_NAME', ''),
        c.code=cgi.escape(request.GET.get('code', str(original_response.status_int))),
        return render('error_document_template.html')

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
    
    def _setup_template_variables(self):
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
            
        log.fatal("%s/%s/%s" % (c.is_sysadmin, c.show_cdo_features, c.cdo_group))      
