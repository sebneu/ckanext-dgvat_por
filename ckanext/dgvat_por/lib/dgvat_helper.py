# -*- coding: utf-8 -*- 
import logging
import re

import sys
sys.path.append("/ckan")
import systemUsers as s 


log = logging.getLogger(__name__)

def generate_user_id(part, gvgid):
    auth_string = part + gvgid
    auth_string = auth_string.lower()
    '''replace " ", ",", ".", "@", ":", "!" ''' 
    auth_string = re.sub("[\ \!,@:\.\?]" , "_" , auth_string)
    '''remove all other chars that are not allowed in usernames'''
    auth_string = re.sub("[^a-z0-9_-]" , "" , auth_string)
    return auth_string  

def normalize_pid(part):
    auth_string = part
    auth_string = auth_string.lower()
    '''replace " ", ",", ".", "@", ":", "!" ''' 
    auth_string = re.sub("[\ \!,@:\.\?]" , "_" , auth_string)
    '''remove all other chars that are not allowed in usernames'''
    auth_string = re.sub("[^a-z0-9_-]" , "" , auth_string)
    return auth_string  

def is_allowed_to_switch(mail):
    return s.is_allowed(mail)

def map_license(license, default = 'cc-by'):
    if license == u'Creative Commons Namensnennung 3.0 Österreich':
      return 'cc-by'
    if license == 'CC-BY-3.0':
      return 'cc-by'
    log.info("helper: map_license() could not find license for %s - is returning default" % license)
    return default

def map_update_frequency(freq):
    if freq:
        #freq = unicode(freq, 'utf8')
        found = [item for item in update_frequency if freq in item]
        if found:
            return found[0][0]
    return None

def map_categorization(cat):
    if cat:
        cat = unicode(cat, 'utf8')
        for c in categorization:
            if t[0] == cat:
                return t[1]
            elif t[1] == cat:
                return t[1]
    return None



update_frequency = [('', ''),
                    ('continual', 'kontinuierlich'),
                    ('daily', 'taeglich', u'täglich'),
                    ('weekly', 'woechentlich', u'wöchentlich'),
                    ('fortnightly', '14-taegig', u'14-tägig'),
                    ('monthly', 'monatlich'),
                    ('quarterly', 'quartalsweise'),
                    ('biannually', 'halbjaehrlich', u'halbjährlich'),
                    ('annually', 'jaehrlich', u'jährlich'),
                    ('asNeeded', 'nach Bedarf', 'bei Bedarf'),
                    ('irregular', 'unregelmaessig', u'unregelmäßig'),
                    ('notPlanned', 'nicht geplant'),
                    ('unknown', 'unbekannt'),]


categorization = [('', ''),
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