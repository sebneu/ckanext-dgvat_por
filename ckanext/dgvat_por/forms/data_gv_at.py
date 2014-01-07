'''
Created on 14.03.2012

@author: BRZ
'''
from ckan import model
from ckan.forms import common
from ckan.forms.builder import FormBuilder
from sqlalchemy.util import OrderedDict

def build_package_dgvat(is_admin=False, user_editable_groups=None,
                              publishers=None,
                              statistics=False,
                              **kwargs):
    builder = FormBuilder(model.Package)
    builder.add_field(common.TextExtraField('meta_data_schema'))
    
    builder.set_field_text('meta_data_schema', instructions='Meta-Data-Schema Instructions', hints="Hint: should be fixed value")
    
    field_groups = OrderedDict([
        (_('Basic information'), ['title', 'name', 'url',
                               'notes', 'license_id', 'tags']),                    
        (_('Resources'), ['resources']),
        (_('Groups'), ['groups']),
        (_('Detail'), ['author', 'author_email',
                       'maintainer', 'maintainer_email',
                       'version', 'meta_data_schemaa',
                       ]),
        (_('Extras'), ['extras']),
        ])
    
    if is_admin:
        field_groups[_('Detail')].append('state')
    builder.set_displayed_fields(field_groups)
    builder.set_label_prettifier(prettify)
    
    return builder
    
def get_dgvat_fieldset(is_admin=False, user_editable_groups=None,
                      publishers=None, **kwargs):
     return build_package_dgvat( \
        is_admin=is_admin, user_editable_groups=user_editable_groups,
        publishers=publishers, **kwargs).get_fieldset()