import urllib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import datetime
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.plugins as p
from ckan.common import _, c
import ckan.plugins.toolkit as toolkit
import urllib2
import logging
import ckan.logic
import __builtin__

import json
import db
abort = base.abort
_get_action = logic.get_action
_check_access = logic.check_access
#log = logging.getLogger('ckanext_apps_and_ideas')
def create_profile_links(context):
    if db.profile_links_table is None:
        db.init_db(context['model'])

@ckan.logic.side_effect_free
def new_link_to_profile(context, data_dict):
    create_profile_links(context)
    info = db.ProfileDatasetLinks()
    info.user_id = data_dict['user_id']
    info.dataset_id = data_dict['dataset_id']
    info.save()
    session = context['session']
    session.add(info)
    session.commit()
    return {"status":"success"} 

@ckan.logic.side_effect_free
def get_links__(context, data_dict):
    create_profile_links(context)
    logging.warning('data_dict')
    logging.warning(data_dict)
    info = db.ProfileDatasetLinks.get(**data_dict)
    logging.warning('info')
    logging.warning(info)
    result = []
    for i in info:
        result.append(i)
    return result
def get_name(dataset_id):
    dataset =  model.Session.query(model.Package).filter(model.Package.id == dataset_id).first()
    return dataset.name
def pkg_id(dataset_name):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}

    dataset = model.Session.query(model.Package).filter(model.Package.name == dataset_name).first()
    if(dataset == None):
        dataset = model.Session.query(model.Package).filter(model.Package.id == dataset_name).first()
    return dataset.id
def get_links(user_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'user_id':user_id}
    return get_links__(context, data_dict)
def valid_dataset(dataset_id):
    dataset = model.Session.query(model.Package).filter(model.Package.id == dataset_id).all()
    return len(dataset) >= 1
def not_id_db(data_dict, context):
    create_profile_links(context)
    info = db.ProfileDatasetLinks.get(**data_dict)
    return len(info) == 0

def logged():
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    if c.userobj:
        return True
    return False
class AddController(base.BaseController):
    
    def add_link(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        dataset_id = base.request.params.get('dataset_id','')
        if c.userobj == None:
            base.abort(401, _('Not authorized'))
        if valid_dataset(dataset_id):
            data_dict = {'dataset_id': dataset_id, 'user_id': c.userobj.id}
        else:
            base.abort(404, _('Dataset not found'))

        if not_id_db(data_dict,context):
        	new_link_to_profile(context, data_dict)

        return h.redirect_to(controller='package', action='read', id=dataset_id)

    def del_link(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        __id = base.request.params.get('id','')
        data_dict = {"id":__id}
        if not_id_db(data_dict, context):
            base.abort(404, _('Dataset not found'))
        create_profile_links(context)
        
        link = db.ProfileDatasetLinks.get(**data_dict)
        if c.userobj.id == link[0].user_id:
            db.ProfileDatasetLinks.delete(**data_dict)
            session = context['session']
            session.commit()
        

        return h.redirect_to(controller="user", action="read", id=c.userobj.name)
