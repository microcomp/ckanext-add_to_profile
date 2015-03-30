import ckan.plugins as plugins

import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import json
import os

import add
import ckan.logic
import ckan.model as model
from ckan.common import _, c
import logging

class AddLinkToProfilePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    def before_map(self, map):
        map.connect('add_link','/add_link', action='add_link', controller='ckanext.add_to_profile.add:AddController')
        map.connect('del_link','/del_link', action='del_link', controller='ckanext.add_to_profile.add:AddController')
        return map

    def get_helpers(self):
        return {'get_links': add.get_links,
        		'dataset_name': add.get_name,
                'logged': add.logged}