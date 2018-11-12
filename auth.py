from flask import session
from flask import current_app as app
import models
from app import db
import requests
from datetime import datetime, timedelta


def newStateToken():
    from uuid import uuid4
    state = str(uuid4())
    session['state_token'] = state
    return state


def is_valid_state(state):
    saved_state = session['state_token']
    if state == saved_state:
        return True
    else:
        return False


def save_session(tokenResponse):
    #TODO: refactor to use loadsession()
    oauth_session = requests.Session()
    oauth_session.headers["X-API-Key"] = app.config['KEY']
    oauth_session.headers["Authorization"] = 'Bearer ' + tokenResponse['access_token']
    oauth_session.headers['User-Agent'] = 'BlackoutX7/pythonDev'
    req = 'https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/'
    res = oauth_session.get(req)
    session['affinityToken'] = res.cookies.get('Q6dA7jjmn3WPGkYAhga2oHvTT+8b849OPtfBrw@@')
    session['destinyMembershipId'] = res.json()['Response']['destinyMemberships'][0]['membershipId'] #TODO: this should be a choice for users with multiple platforms
    session['membershipType'] = res.json()['Response']['destinyMemberships'][0]['membershipType']
    session['displayName'] = res.json()['Response']['destinyMemberships'][0]['displayName']
    session['access_token'] = tokenResponse['access_token']
    session['refresh_token'] = tokenResponse['refresh_token']
    session['refresh_ready'] = datetime.now() + timedelta(seconds=int(tokenResponse['expires_in']))
    session['refresh_expired'] = datetime.now() + timedelta(seconds=int(tokenResponse['refresh_expires_in']))
    usercheck = models.User.query.filter_by(membershipId=session['destinyMembershipId']).first()
    if usercheck:
        session['UserId'] = usercheck.id
    else:
        newuser = models.User(membershipId=session['destinyMembershipId'])
        db.session.add(newuser)
        db.session.commit()
        session['UserId'] = newuser.id


def get_token(code):
    HEADERS = app.config['HEADERS']
    HEADERS['Content-Type'] = 'application/x-www-form-urlencoded'
    post_data = {'grant_type': 'authorization_code',
                 'code': code,
                 'client_id': app.config['CLIENT_ID'],
                 'client_secret': app.config['CLIENT_SECRET']}
    response = requests.post(app.config['ACCESS_TOKEN_URL'], data=post_data, headers=HEADERS)
    return response.json()


def load_session(access_token):
    oauth_session = requests.session()
    oauth_session.headers["X-API-Key"] = app.config['KEY']
    oauth_session.headers["Authorization"] = 'Bearer ' + access_token
    oauth_session.headers['User-Agent'] = 'BlackoutX7/pythonDev'
    a = requests.cookies.create_cookie(name='Q6dA7jjmn3WPGkYAhga2oHvTT+8b849OPtfBrw@@', value=session['affinityToken'], domain='www.bungie.net', path='/')
    oauth_session.cookies.set_cookie(a)
    return oauth_session


def refreshToken():
    refresh_token = session['refresh_token']
    ready = session['refresh_ready']
    expired = session['refresh_expired']
    if (ready < datetime.now()) or (expired > datetime.now()):
        return
    else:
        HEADERS = app.config['HEADERS']
        HEADERS['Content-Type'] = 'application/x-www-form-urlencoded'
        post_data = {'grant_type': 'refresh_token',
                     'refresh_token': refresh_token,
                     'client_id': app.config['CLIENT_ID'],
                     'client_secret': app.config['CLIENT_SECRET']}
        response = requests.post(app.config['ACCESS_TOKEN_URL'], data=post_data, headers=HEADERS)
        save_session(response.json())
    return None





