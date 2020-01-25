# -*- coding: utf-8 -*-
from copy import deepcopy
import re
import json
from scrapy.http import HtmlResponse
import scrapy
from urllib.parse import urlencode
from teachers.les5.gbparse.items import FollowersItem, FollowingItem

HASHES = {
    'followers': 'c76146de99bb02f6415203be841dd25a',
    'following': 'd04b0a864b4b54837c0d870b0e77e076',
    'media': '58b6785bea111c67129decbe6a448951',
    'media_comments': '97b41c52301f77ce508f55e66d17620e',
    'likes': 'd5d763b1e2acf209d62d22d184488e57',
    'tags': '174a5243287c5f3a7de741089750ab3b',

}
# переход на следующую страницу - с помощью end-cursor
class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://instagram.com/']
    insta_login = 'besmartbee'
    inst_pass = 'gurubee2020'
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    parse_user = 'gefestart'
    graphql_url = 'https://www.instagram.com/graphql/query/?'
    user_data_hash = 'c9100bf9110dd6361671f113dd02e7d6'

    def parse(self, response: HtmlResponse):
        csrf_token = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.user_parse,
            formdata={'username': self.insta_login, 'password': self.inst_pass},
            headers={'X-CSRFToken': csrf_token}
        )

    def user_parse(self, response: HtmlResponse):
        j_body = json.loads(response.text)
        if j_body['authenticated']:
            yield response.follow(
                f'/{self.parse_user}',
                callback=self.userdata_parse,
                cb_kwargs={'username': self.parse_user}
            )

    def userdata_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        varibles = {
            'id': user_id,
            "include_reel": True,
            "include_logged_out_extras": False,
            "first": 12,
        }
        url = f'{self.graphql_url}query_hash={self.user_data_hash}&{urlencode(varibles)}'

        url_followers = f'{self.graphql_url}query_hash={HASHES["followers"]}&{urlencode(varibles)}'
        yield response.follow(
            url_followers,
            callback=self.user_followers_parse,
            cb_kwargs={'username': username,
                       'user_id': user_id,
                       'varibles': deepcopy(varibles)}
        )

        url_following = f'{self.graphql_url}query_hash={HASHES["following"]}&{urlencode(varibles)}'
        yield response.follow(
            url_following,
            callback=self.user_following_parse,
            cb_kwargs={'username': username,
                       'user_id': user_id,
                       'varibles': deepcopy(varibles)}
        )

    def user_data(self, response: HtmlResponse, username):
        j_user_data = json.loads(response.text)
        print(1)

    def user_followers_parse(self, response: HtmlResponse, username, user_id, varibles):
        j_data = json.loads(response.text)
        page_info = j_data.get('data').get('user').get('edge_followed_by').get('page_info')
        if page_info.get('has_next_page'):
            varibles['after'] = page_info.get('end_cursor')

            url_followers = f'{self.graphql_url}query_hash={HASHES["followers"]}&{urlencode(varibles)}'
            yield response.follow(
                url_followers,
                callback=self.user_followers_parse,
                cb_kwargs={'username': username,
                           'user_id': user_id,
                           'varibles': deepcopy(varibles),
                           }
            )

        for follower in j_data.get('data').get('user').get('edge_followed_by').get('edges'):
            item = FollowersItem(user_name=username,
                                 user_id=user_id,
                                 follower_id=follower['node']['id'],
                                 follower_name=follower['node']['username'],
                                 data=follower['node']
                                 )
            yield item

    def user_following_parse(self, response: HtmlResponse, username, user_id, varibles):
        j_data = json.loads(response.text)
        page_info = j_data.get('data').get('user').get('edge_follow').get('page_info')
        if page_info.get('has_next_page'):
            varibles['after'] = page_info.get('end_cursor')

            url_following = f'{self.graphql_url}query_hash={HASHES["following"]}&{urlencode(varibles)}'
            yield response.follow(
                url_following,
                callback=self.user_following_parse,
                cb_kwargs={'username': username,
                           'user_id': user_id,
                           'varibles': deepcopy(varibles),
                           }
            )

        for followings in j_data.get('data').get('user').get('edge_follow').get('edges'):
            item = FollowingItem(user_name=username,
                                 user_id=user_id,
                                 following_id=followings['node']['id'],
                                 following_name=followings['node']['username'],
                                 data=followings['node']
                                 )
            yield item

    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')
