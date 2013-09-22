import re
import requests

from adnpy.consts import (PAGINATION_PARAMS, POST_PARAMS, USER_PARAMS, USER_SEARCH_PARAMS, POST_SEARCH_PARAMS,
                          CHANNEL_PARAMS, MESSAGE_PARAMS, PLACE_SEARCH_PARAMS)
from adnpy.errors import (AdnAuthAPIException, AdnPermissionDenied, AdnMissing, AdnRateLimitAPIException,
                          AdnInsufficientStorageException, AdnAPIException)
from adnpy.models import (SimpleValueModel, APIModel, Post, User, Channel, Message, Interaction,
                         Token, Place, ExploreStream)
from adnpy.utils import json_encoder

class API(requests.Session):

    @classmethod
    def build_api(cls, api_root='https://alpha-api.app.net/stream/0', access_token=None):
        api = cls()
        api.api_root = api_root
        if access_token:
            api.add_authorization_token(access_token)

        return api

    def request(self, method, url, *args, **kwargs):
        if url:
            url =  self.api_root + url

        response = super(API, self).request(method, url, *args, **kwargs)

        response = APIModel.from_string(response.content, self)

        if response.meta.code == 401:
            raise AdnAuthAPIException(response)

        if response.meta.code == 403:
            raise AdnPermissionDenied(response)

        if response.meta.code == 404:
            raise AdnMissing(response)

        if response.meta.code == 429:
            raise AdnRateLimitAPIException(response)

        if response.meta.code == 507:
            raise AdnInsufficientStorageException(response)

        if response.meta.code != 200:
            raise AdnAPIException(response)

        return response

    def add_authorization_token(self, token):
        self.headers.update({
            'Authorization': 'Bearer %s' % (token),
        })

    def request_json(self, method, *args, **kwargs):
        kwargs.setdefault('headers', dict())
        kwargs['headers'].update({'Content-Type': 'application/json'})
        if kwargs.get('data'):
            kwargs['data'] = json_encoder(kwargs['data'])

        return self.request(method, *args, **kwargs)


re_path_template = re.compile('{\w+}')


def bind_api_method(func_name, path, payload_type=None, payload_list=False, allowed_params=None, method='GET', require_auth=True, content_type='JSON'):
    allowed_params = allowed_params or []

    def run(self, *args, **kwargs):
        parameters = {}
        for key, val in kwargs.items():
            if key in allowed_params:
                parameters[key] = kwargs.pop(key)

        proccessed_path = path
        path_args = re_path_template.findall(path)
        for variable in path_args:
            args = list(args)
            try:
                value = args.pop(0)
            except IndexError:
                raise Exception('Not enough positional arguments expects: %s' % (path_args))

            value = unicode(getattr(value, 'id', value))
            proccessed_path = proccessed_path.replace(variable, value)
        resp_method = self.request
        if method in ('POST', 'PUT', 'PATCH') and content_type == 'JSON' and kwargs.get('data'):
            resp_method = self.request_json

        resp = resp_method(method, proccessed_path, params=parameters, **kwargs)
        if payload_list:
            resp.data = [payload_type.from_response_data(x, api=self) for x in resp.data]
        else:
            resp.data = payload_type.from_response_data(resp.data, api=self)

        return resp.data, resp.meta

    setattr(API, func_name, run)

# Post methods

bind_api_method('write_post', '/posts', payload_type=Post, method='POST',
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('get_post', '/posts/{post_id}', payload_type=Post,
                allowed_params=POST_PARAMS,
                require_auth=False)


bind_api_method('delete_post', '/posts/{post_id}', payload_type=Post, method='DELETE',
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('repost_post', '/posts/{post_id}/repost', payload_type=Post, method='POST',
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('unrepost_post', '/posts/{post_id}/repost', payload_type=Post, method='DELETE',
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('star_post', '/posts/{post_id}/star', payload_type=Post, method='POST',
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('unstar_post', '/posts/{post_id}/star', payload_type=Post, method='DELETE',
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('get_posts', '/posts', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS + ['ids'],
                require_auth=True)


bind_api_method('users_posts', '/users/{user_id}/posts', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=True)


bind_api_method('users_starred_posts', '/users/{user_id}/stars', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=True)


bind_api_method('users_mentioned_posts', '/users/{user_id}/mentions', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=True)


bind_api_method('posts_with_hashtag', '/posts/tag/{hashtag}', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=False)


bind_api_method('posts_replies', '/posts/{post_id}/replies', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=True)


bind_api_method('users_post_stream', '/posts/stream', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=True)


bind_api_method('users_post_stream_unified', '/posts/stream/unified', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=True)


bind_api_method('posts_stream_global', '/posts/stream/global', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=False)


bind_api_method('report_post', '/posts/{post_id}/report', payload_type=Post,
                allowed_params=POST_PARAMS,
                require_auth=True)


bind_api_method('post_search', '/posts/search', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS + POST_SEARCH_PARAMS,
                require_auth=True)


# User methods

bind_api_method('get_user', '/users/{user_id}', payload_type=User,
                allowed_params=USER_PARAMS,
                require_auth=False)


bind_api_method('get_users', '/users', payload_type=User, payload_list=True,
                allowed_params=PAGINATION_PARAMS + USER_PARAMS + ['ids'],
                require_auth=False)


bind_api_method('update_user', '/users/{user_id}', payload_type=User, method='PUT',
                allowed_params=USER_PARAMS,
                require_auth=True)


bind_api_method('patch_user', '/users/{user_id}', payload_type=User, method='PATCH',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('update_avatar', '/users/me/avatar', payload_type=User, method='POST',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('update_cover', '/users/me/cover', payload_type=User, method='POST',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('follow_user', '/users/{user_id}/follow', payload_type=User, method='POST',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('unfollow_user', '/users/{user_id}/follow', payload_type=User, method='DELETE',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('mute_user', '/users/{user_id}/mute', payload_type=User, method='POST',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('unmute_user', '/users/{user_id}/mute', payload_type=User, method='DELETE',
                 allowed_params=USER_PARAMS,
                 require_auth=True)



bind_api_method('block_user', '/users/{user_id}/block', payload_type=User, method='POST',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('unblock_user', '/users/{user_id}/block', payload_type=User, method='DELETE',
                 allowed_params=USER_PARAMS,
                 require_auth=True)


bind_api_method('user_search', '/users/search', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS + USER_SEARCH_PARAMS,
                 require_auth=True)


bind_api_method('users_following', '/users/{user_id}/following', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_followers', '/users/{user_id}/followers', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_following_ids', '/users/{user_id}/following/ids', payload_type=SimpleValueModel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_followers_ids', '/users/{user_id}/followers/ids', payload_type=SimpleValueModel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_muted_users', '/users/{user_id}/muted', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_muted_users_ids', '/users/{user_id}/muted', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_blocked_users', '/users/{user_id}/blocked', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_blocked_users_ids', '/users/blocked/ids', payload_type=SimpleValueModel, payload_list=True,
                 allowed_params=USER_PARAMS + ['ids'],
                 require_auth=True)


bind_api_method('users_reposted_post', '/posts/{post_id}/reposters', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


bind_api_method('users_starred_post', '/posts/{post_id}/stars', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + USER_PARAMS,
                 require_auth=True)


# Channels
bind_api_method('subscribed_channels', '/channels', payload_type=Channel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('create_channel', '/channels', payload_type=Channel, method='POST',
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('get_channel', '/channels/{channel_id}', payload_type=Channel,
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('get_channels', '/channels', payload_type=Channel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + CHANNEL_PARAMS + ['ids'],
                 require_auth=True)


bind_api_method('users_channels', '/users/me/channels', payload_type=Channel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('num_unread_pm_channels', '/users/me/channels/pm/num_unread', payload_type=SimpleValueModel,
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('update_channel', '/channels/{channel_id}', payload_type=Channel, method='PUT',
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('subscribe_channel', '/channels/{channel_id}/subscribe', payload_type=Channel, method='POST',
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('unsubscribe_channel', '/channels/{channel_id}/subscribe', payload_type=Channel, method='DELETE',
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)


bind_api_method('subscribed_users', '/channels/{channel_id}/subscribers', payload_type=User, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + CHANNEL_PARAMS,
                 require_auth=True)

bind_api_method('subscribed_user_ids', '/channels/{channel_id}/subscribers/ids', payload_type=SimpleValueModel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + CHANNEL_PARAMS,
                 require_auth=True)

bind_api_method('subscribed_user_ids_for_channels', '/channels/subscribers/ids', payload_type=SimpleValueModel,
                 allowed_params=CHANNEL_PARAMS + ['ids'],
                 require_auth=True)

bind_api_method('mute_channel', '/channels/{channel_id}/mute', payload_type=Channel, method='POST',
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)

bind_api_method('unmute_channel', '/channels/{channel_id}/mute', payload_type=Channel, method='POST',
                 allowed_params=CHANNEL_PARAMS,
                 require_auth=True)

bind_api_method('muted_channels', '/users/me/channels/muted', payload_type=Channel, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + CHANNEL_PARAMS,
                 require_auth=True)


# Messages
bind_api_method('get_messages', '/channels/{channel_id}/messages', payload_type=Message, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + MESSAGE_PARAMS,
                 require_auth=True)


bind_api_method('create_message', '/channels/{channel_id}/messages', payload_type=Message, method='POST',
                 allowed_params=MESSAGE_PARAMS,
                 require_auth=True)


bind_api_method('get_message', '/channels/{channel_id}/messages/{message_id}', payload_type=Message,
                 allowed_params=MESSAGE_PARAMS,
                 require_auth=True)


bind_api_method('get_messages', '/channels/messages', payload_type=Message, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + MESSAGE_PARAMS + ['ids'],
                 require_auth=True)


bind_api_method('users_messages', '/users/me/messages', payload_type=Message, payload_list=True,
                 allowed_params=PAGINATION_PARAMS + MESSAGE_PARAMS,
                 require_auth=True)


bind_api_method('delete_message', '/channels/{channel_id}/messages/{message_id}', payload_type=Message, method='DELETE',
                 allowed_params=PAGINATION_PARAMS + MESSAGE_PARAMS + ['ids'],
                 require_auth=True)


# Interactions
bind_api_method('interactions_with_user', '/users/me/interactions', payload_type=Interaction, payload_list=True,
                 allowed_params=PAGINATION_PARAMS,
                 require_auth=True)


# Text Process
bind_api_method('text_process', '/text/process', payload_type=APIModel, method='POST',
                 require_auth=True)


# Token
bind_api_method('get_token', '/token', payload_type=Token,
                 require_auth=True)


# Config
bind_api_method('get_config', '/config', payload_type=APIModel,
                require_auth=True)


# Places
bind_api_method('get_place', '/places/{factual_id}', payload_type=Place,
                require_auth=True)


bind_api_method('search_places', '/places/search', payload_type=Place, payload_list=True,
                allowed_params=PAGINATION_PARAMS + PLACE_SEARCH_PARAMS,
                require_auth=True)


# Explore Streams
bind_api_method('get_explore_streams', '/posts/stream/explore', payload_type=ExploreStream, payload_list=True,
                require_auth=False)


bind_api_method('get_explore_stream', '/posts/stream/explore/{slug}', payload_type=Post, payload_list=True,
                allowed_params=PAGINATION_PARAMS + POST_PARAMS,
                require_auth=False)
