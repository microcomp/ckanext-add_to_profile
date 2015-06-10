# -*- coding: utf-8 -*-
import urllib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import datetime
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic.converters as conv
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
log = logging.getLogger(__name__)

def _get_user_followers(user_id):
    context_follow = {'ignore_auth' : True}
    followers = toolkit.get_action('user_follower_list')(context_follow, {'id' : user_id})
    users = []
    for follower in followers:
        user_obj = model.User.get(follower['id'])
        #we need to get userobj to get email
        if user_obj:
            users.append((user_obj.email, user_obj.fullname))
    return users
        
        
def link_profile_notification(context, data_dict):
    dataset_id = data_dict['dataset_id']
    userobj = model.User.get(data_dict['user_id'])
    action = data_dict['action']
    recipients = [(userobj.email, userobj.fullname)]
    pkg = model.Package.get(dataset_id)
    
    if pkg and userobj and not pkg.private:
        recipients = recipients + _get_user_followers(userobj.id)
    dataset_read_url = toolkit.url_for(controller='package', action='read',id=dataset_id)
    if action == 'added':
        message_action = u'pridal'
        subject = _('Notification: link added to user profile {0}')
    elif action == 'deleted':
        message_action = u'odstránil'
        subject = _('Notification: link deleted from user profile {0}')
    subject = subject.format(userobj.fullname)
    message=u'''
Dobrý deň {name},
oznamujeme Vám, že používateľ {profile_name} {action} odkaz vo svojom profile na dataset {pkg_name}.
V systýme MOD je tento dataset dostupný na URL adrese: {url} .

Tento email Vám bol vygenerovaný automaticky, preto naň, prosím, neodpisujte.
   
{signature}
'''
    message = message.format(name = '{name}', signature = '{signature}', profile_name = userobj.fullname, action=message_action, pkg_name = pkg.title, url = dataset_read_url)
    log.info('message template: %s', message)
    data_notification = {'entity_id' : userobj.id,
                         'entity_type' : 'user',
                         'subject' : subject,
                         'message' : message,
                         'recipients' : recipients}
    toolkit.get_action('send_general_notification')(context, data_notification)
    
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
    if is_resource(dataset_id):
        return False
    context = {'model': model, 'session': model.Session,'user': c.user or c.author, 'auth_user_obj': c.userobj,'for_view': True}
    dat_id  = conv.convert_package_name_or_id_to_id(dataset_id, context)
    dataset = model.Session.query(model.Package).filter(model.Package.id == dat_id).all()

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

def inprof(dataset_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    try:
        data_dict = {'user_id': c.userobj.id, 'dataset_id': conv.convert_package_name_or_id_to_id(dataset_id, context)}
        create_profile_links(context)
        info = db.ProfileDatasetLinks.get(**data_dict)
        return len(info) > 0
    except AttributeError:
        return False
def is_resource(resource_id):
    resource_group_id = model.Session.query(model.Resource).filter(model.Resource.id == resource_id).all()
    return len(resource_group_id) > 0

def get_dataset_id(resource_id):
    resource_group_id = model.Session.query(model.Resource).filter(model.Resource.id == resource_id).first().resource_group_id
    package_id = model.Session.query(model.ResourceGroup).filter(model.ResourceGroup.id == resource_group_id).first().package_id
    return package_id
class AddController(base.BaseController):
    
    def add_link(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        dataset_id = base.request.params.get('dataset_id','')
        if c.userobj == None:
            base.abort(401, _('Not authorized'))
        if valid_dataset(conv.convert_package_name_or_id_to_id(dataset_id, context)):
            data_dict = {'dataset_id': conv.convert_package_name_or_id_to_id(dataset_id, context), 'user_id': c.userobj.id}
        else:
            base.abort(404, _('Dataset not found'))

        if not_id_db(data_dict,context):
            new_link_to_profile(context, data_dict)
            data_dict['action'] = 'added'
            link_profile_notification(context, data_dict)

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
            dataset_id = link[0].dataset_id
            db.ProfileDatasetLinks.delete(**data_dict)
            session = context['session']
            session.commit()
            data_notification = {'dataset_id' : dataset_id, 'user_id' : c.userobj.id, 'action' : 'deleted'}
            link_profile_notification(context, data_notification)
            
        

        return h.redirect_to(controller="user", action="read", id=c.userobj.name)
