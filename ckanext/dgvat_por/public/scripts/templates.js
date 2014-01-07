var CKAN = CKAN || {};  
CKAN.Templates = CKAN.Templates || {};

CKAN.Templates.resourceUpload = ' \
<div class="fileupload"> \
  <form action="http://test-ckan-net-storage.commondatastorage.googleapis.com/" class="resource-upload" \
    enctype="multipart/form-data" \
    method="POST"> \
 \
    <div class="hidden-inputs"></div> \
    <input type="file" name="file" /> \
    <br /> \
    <div class="fileinfo"></div> \
    <input id="upload" name="add-resource-upload" type="submit" class="btn btn-primary" value="'+CKAN.Strings.upload+'" /> \
  </form> \
  <div class="alert alert-block" style="display: none;"></div> \
</div>';
  


CKAN.Templates.resourceEntry = ' \
  <li class="ui-state-default resource-edit drag-bars"> \
    <a class="resource-open-my-panel" href="#">\
      <img class="js-resource-icon inline-icon resource-icon" src="${resource_icon}" /> \
      <span class="js-resource-edit-name">${resource.name}</span>\
    </a>\
  </li>';

var youCanUseMarkdownString = CKAN.Strings.youCanUseMarkdown.replace('%a', '<a href="http://daringfireball.net/projects/markdown/syntax" target="_blank">').replace('%b', '</a>');
var shouldADataStoreBeEnabledString = CKAN.Strings.shouldADataStoreBeEnabled.replace('%a', '<a href="http://docs.ckan.org/en/latest/datastore.html" target="_blank">').replace('%b', '</a>');
var datesAreInISOString = CKAN.Strings.datesAreInISO.replace('%a', '<a href="http://en.wikipedia.org/wiki/ISO_8601#Calendar_dates" target="_blank">').replace('%b', '</a>').replace('%c', '<strong>').replace('%d', '</strong>');

// TODO it would be nice to unify this with the markdown editor specified in helpers.py
CKAN.Templates.resourceDetails = ' \
  <div style="display: none;" class="resource-details"> \
    <div class="flash-messages"> \
      <div class="alert alert-error resource-errors"></div> \
    </div> \
    <div class="control-group"> \
      <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Bezeichner</label> \
      <div class="controls" property="rdf:value"> \
        <input class="js-resource-edit-name" name="resources__${num}__name" type="text" value="${resource.name}" class="long" /> \
      </div> \
    </div> \
    <div class="control-group {{if resource.url_error}} error{{/if}}"> \
      <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Link</label> \
      <div class="controls"> \
        {{if resource.resource_type=="file.upload"}} \
          ${resource.url} \
          <input name="resources__${num}__url" type="hidden" value="${resource.url}" /> \
        {{/if}} \
        {{if resource.resource_type!="file.upload"}} \
          <input name="resources__${num}__url" type="text" value="${resource.url}" class="long" title="${resource.url_error}" /> \
        {{/if}} \
      </div> \
    </div> \
    <div class="control-group"> \
      <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Format\
          &nbsp;&nbsp;<img class="js-resource-icon inline-icon resource-icon" src="${resource_icon}" /> </label>\
      <div class="controls"> \
        <input name="resources__${num}__format" type="text" value="${resource.format}" class="long js-resource-edit-format autocomplete-format" placeholder="'+CKAN.Strings.resourceFormatPlaceholder+'" /> \
      </div> \
    </div> \
    <div class="control-group"> \
      <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Typ</label> \
      <div class="controls"> \
        {{if resource.resource_type=="file.upload"}} \
          '+CKAN.Strings.dataFileUploaded+' \
          <input name="resources__${num}__resource_type" type="hidden" value="${resource.resource_type}" /> \
        {{/if}} \
        {{if resource.resource_type!="file.upload"}} \
          <select name="resources__${num}__resource_type" class="short"> \
            {{each resourceTypeOptions}} \
            <option value="${$value[0]}" {{if $value[0]==resource.resource_type}}selected="selected"{{/if}}>${$value[1]}</option> \
            {{/each}} \
          </select> \
        {{/if}} \
      </div> \
    </div> \
    <div class="control-group datastore-enabled  ckan-sysadmin"> \
      <label for="" class="control-label" property="rdfs:label">'+CKAN.Strings.datastoreEnabled+'</label> \
      <div class="controls"> \
        <label class="checkbox"> \
          <input type="checkbox" class="js-datastore-disabled-checkbox" /> \
          <input type="hidden" name="resources__${num}__webstore_url" value="${resource.webstore_url}" class="js-datastore-enabled-text" /> \
          <span class="hint">'+shouldADataStoreBeEnabledString+'</span> \
        </label> \
      </div> \
    </div> \
    <div class="control-group"> \
      <label for="" class="control-label" property="rdfs:label">Ver&ouml;ffentlichungsdatum</label> \
      <div class="controls"> \
        <input type="text" value="${resource.created}" name="resources__${num}__created" class="input-small resource_date" /> \
        <div class="hint">Datum im ISO Format YYYY-MM-DD zB. 2012-12-25</div> \
      </div> \
    </div> \
    <div class="control-group"> \
      <label for="" class="control-label" property="rdfs:label">&Auml;nderungsdatum</label> \
      <div class="controls"> \
        <input class="input-small resource_date" name="resources__${num}__last_modified" type="text" value="${resource.last_modified}" /> \
        <div class="hint">Datum im ISO Format YYYY-MM-DD zB. 2012-12-25</div> \
      </div> \
    </div> \
    <div class="control-group"> \
      <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Gr&ouml;&szlig;e in Bytes</label> \
      <div class="controls"> \
        <input name="resources__${num}__size" type="text" value="${resource.size}" class="long" /> \
      </div> \
    </div> \
    <div class="control-group ckan-sysadmin"> \
      <label for="" class="control-label" property="rdfs:label">'+CKAN.Strings.mimetype+'</label> \
      <div class="controls"> \
        <input name="resources__${num}__mimetype" type="text" value="${resource.mimetype}" /> \
      </div> \
    </div> \
    <div class="control-group ckan-sysadmin"> \
      <label for="" class="control-label" property="rdfs:label">'+CKAN.Strings.mimetypeInner+'</label> \
      <div class="controls"> \
        <input name="resources__${num}__mimetype_inner" type="text" value="${resource.mimetype_inner}" /> \
      </div> \
    </div> \
    <div class="control-group ckan-sysadmin"> \
      <label for="" class="control-label" property="rdfs:label">'+CKAN.Strings.id+'</label> \
      <div class="controls"> \
        <input type="text" disabled="disabled" value="${resource.id}" class="disabled" /> \
        <input name="resources__${num}__id" type="hidden" value="${resource.id}" /> \
      </div> \
    </div> \
    <div class="control-group ckan-sysadmin"> \
      <label for="" class="control-label" property="rdfs:label">'+CKAN.Strings.hash+'</label> \
      <div class="controls"> \
        <input type="text" disabled="disabled" class="disabled" value="${resource.hash || "'+CKAN.Strings.unknown+'"}"/> \
        <input name="resources__${num}__hash" type="hidden" value="${resource.hash}" /> \
      </div> \
    </div> \
    <div class="control-group"> \
    <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Sprache</label> \
    <div class="controls"> \
      <input name="resources__${num}__language" type="text" value="${resource.language}" /> \
    </div> \
  </div> \
  <div class="control-group"> \
  <label for="" class="control-label" property="rdfs:label">Datensatz/Dienst Character Set Code</label> \
  <div class="controls"> \
    <input name="resources__${num}__characterset" type="text" value="${resource.characterset}" /> \
  </div> \
</div> \
    <div class="control-group"> \
    <!--      <label class="control-label ckan-sysadmin">'+CKAN.Strings.extraFields+' \
        <button class="btn btn-small add-resource-extra">'+CKAN.Strings.addExtraField+'</button>\
      </label>\
      <div class="controls"> \
        <div class="dynamic-extras"> \
        </div> \
      </div> -->\
    <button class="btn btn-danger resource-edit-delete js-resource-edit-delete">Datensatz/Dienst l&ouml;schen</button>\
  </div> \
';

CKAN.Templates.resourceExtra = ' \
  <div class="dynamic-extra"> \
  <button class="btn btn-danger remove-resource-extra">X</button>\
  <input type="text" placeholder="Key" class="extra-key" value="${key}" /> \
  <input type="text" placeholder="Value" class="extra-value" value="${value}" /> \
  </div> \
  ';