from flask import Flask
from flask import render_template, request, redirect, url_for, session, abort, flash, g
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import logging

# BEFORE Submitting


# IF Time Allows
#TODO: Users with 2 membershiptypes not given a choice.
#TODO: move routes to another file
#TODO: Reinvestigate view/save current
#TODO: implement user friendly edit

#OBE - Will not be able to rebuild in time

#TODO: Auth is ~~completely~~ partially broken in prod >
    # can Equip/Transfer but not process needs to access inventory >
    #  Also would require that the user have already built Loadouts >
    # Workaround: Enable Show my non equipped Inventory on Bungie > Settings > Privacy
    # This may be a result of the use of Session to rebuild to oauth_session

#TODO: add sockets to loadout view >
    # Requires rework of Saved data structure to include Sockets info
    # Saved loadouts contain un-API-filled Items (only Manifest Data)
    # Settled for Name and FlavorText

#TODO: Manifest update breaks loadouts table (next manifest 11/27) >
    # Manifest file must be updated manually with a restart,
    # Restarting the app was clearing loadouts, thus breaking
    # May have repaired the database drop

# APP Setup
app = Flask(__name__)
Bootstrap(app)
app.config.from_object('config-dev')
# app.config.from_object('config-prod')
db = SQLAlchemy(app)
import models
app.config['SESSION_SQLALCHEMY'] = db
Session(app)
import requests_cache, json
import destiny
import auth
from functools import wraps

# Cache Setup
requests_cache.install_cache(cache_name='DestinyAPI', backend='sqlite', expire_after=60,
                             allowable_codes=(200,), allowable_methods=('GET',))

# Function Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated_function


# App Routes

'''
Main Routes: Handle the main page and OAuth flow with Bungie
'''
@app.route('/')
@login_required
def dashboard():
    #INJECT Loading here
    loadouts = models.Loadout.query.filter_by(userid=session['UserId']).all()
    return render_template('dashboard.html', loadouts=loadouts)


@app.route('/login')
def login():
    state = auth.newStateToken()
    url = app.config['AUTH_URL'] +'&state=' + state
    return render_template('login.html', url=url)


@app.route('/bungie/callback')
def bungie_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if auth.is_valid_state(state):
        session.pop('state_token', None)
        tokenResponse = auth.get_token(code)
        auth.save_session(tokenResponse)
        return redirect(url_for("dashboard"))
    else:
        abort(403)


'''
Loadout Routes : CRUD routes for the Loadout data object
'''


@app.route('/loadout/view', methods=["POST"])
def loadout():
    id = request.form.get('loadoutid')
    if id:
        loadout = models.Loadout.query.filter_by(id=id).first()
        if loadout:
            equip = json.loads(loadout.loadout)
            items = []
            for item in equip:
                a = destiny.Item(**item)
                items.append(a)
            return render_template('loadout.html', items=items)
        else:
            flash(message='Loadout Not Found: You must select a valid Loadout', category='danger')
            return redirect(url_for('dashboard'))
    else:
        flash(message='No Loadout Selected: You must select a valid Loadout', category='danger')
        return redirect(url_for('dashboard'))


@app.route('/loadout/save', methods=["POST"])
def saveLoadout():
    items = []
    char = request.form.get("characterId")
    primary = request.form.get("primaryWeapon")
    energy = request.form.get("secondaryWeapon")
    power = request.form.get("heavyWeapon")
    helmet = request.form.get("helmetArmor")
    arms = request.form.get("armsArmor")
    chest = request.form.get("chestArmor")
    legs = request.form.get("legArmor")
    classitem = request.form.get("classArmor")

    if not char:
        flash(message="No character selected", category="danger")
        return redirect(url_for('dashboard'))
    if all((primary, energy, power, helmet, arms, chest, legs, classitem)):
        for j in (primary, energy, power, helmet, arms, chest, legs, classitem):
            j = j.replace('\'', '\"')
            i = json.loads(j.strip('\''))
            # This would need to make 8 calls for GetItem to store full Items for Sockets on View
            itemc = destiny.Item(i['itemHash'], i['itemInstanceId'])
            items.append(itemc.__dict__)
        if destiny.validateLoadout(items):
            save = models.Loadout(session['UserId'], char, str(json.dumps(items)))
            db.session.add(save)
            db.session.commit()
            flash("Loadout {} Saved!".format(save.id), category="info")
            return redirect(url_for('dashboard'))
        else: # Not validated
            flash("Loadout Invalid: Too many Exotics", "danger")
            return redirect(url_for('dashboard'))
    else: # not all()
        flash("Loadout Error: Missing items in loadout", category="danger")
        return redirect(url_for('dashboard'))


'''
Building Loadout: 2 step process, Character passed to Inventory passed to save above
'''

@app.route('/builder', methods=["GET"])
@login_required
def charselect():
    oauth_session = auth.load_session(session['access_token'])
    chars = []
    # Storing data in Session helps with subsequent load times.
    if "characterIds" not in session:
        res = destiny.getProfile(oauth_session, session['membershipType'],
                                 session['destinyMembershipId'], destiny.COMPONENTS['Profiles'])
        session["characterIds"] = res['profile']['data']['characterIds']
        if "characters" not in session:
            chars = destiny.getCharacterInfo(oauth_session, session['membershipType'],
                                             session['destinyMembershipId'], session['characterIds'])
            session["characters"] = chars.toJSON()
    if not isinstance(chars,destiny.CharacterList):
        chars = destiny.CharacterList(json.loads(session["characters"])["chars"])
    return render_template('charselect.html', characters=chars.chars)


@app.route('/builder/items', methods=["POST"])
@login_required
def builder():
    charid = request.form.get("charid")
    classname = request.form.get("classname")
    oauth_session = auth.load_session(session['access_token'])
    # Same session Storage as character WAY faster if stored, but lacks new items
    if 'inventory' not in session:
        inventory = destiny.buildInventory(oauth_session, session['membershipType'], session['destinyMembershipId'])
        session['inventory'] = inventory.toJSON()
    else:
        x = json.loads(session['inventory'].strip('\''))
        inventory = destiny.Inventory(**x)
    flash('Inventory Loaded', 'info')
    if classname == "Hunter":
        return render_template('builder.html', characterId=charid, primaryWeapons=inventory.kinetic,
                               secondaryWeapons=inventory.energy,
                               heavyWeapons=inventory.power,
                               helmetArmor=inventory.hunterArmor['HelmetArmor'],
                               armsArmor=inventory.hunterArmor["ArmsArmor"],
                               chestArmor=inventory.hunterArmor["ChestArmor"],
                               legArmor=inventory.hunterArmor["LegArmor"],
                               classArmor=inventory.hunterArmor["ClassArmor"])
    if classname == "Warlock":
        return render_template('builder.html', characterId=charid, primaryWeapons=inventory.kinetic,
                               secondaryWeapons=inventory.energy,
                               heavyWeapons=inventory.power,
                               helmetArmor=inventory.warlockArmor['HelmetArmor'],
                               armsArmor=inventory.warlockArmor["ArmsArmor"],
                               chestArmor=inventory.warlockArmor["ChestArmor"],
                               legArmor=inventory.warlockArmor["LegArmor"],
                               classArmor=inventory.warlockArmor["ClassArmor"])
    if classname == "Titan":
        return render_template('builder.html', characterId=charid, primaryWeapons=inventory.kinetic,
                               secondaryWeapons=inventory.energy,
                               heavyWeapons=inventory.power,
                               helmetArmor=inventory.titanArmor['HelmetArmor'],
                               armsArmor=inventory.titanArmor["ArmsArmor"],
                               chestArmor=inventory.titanArmor["ChestArmor"],
                               legArmor=inventory.titanArmor["LegArmor"],
                               classArmor=inventory.titanArmor["ClassArmor"])


@app.route('/loadout/equip', methods=["POST"])
@login_required
def equipLoadout():
    id = request.form.get("loadoutid")
    oauth_session = auth.load_session(session['access_token'])
    loadout = models.Loadout.query.filter_by(id=id).first()
    try:
        destiny.equipLoadout(oauth_session, session['membershipType'], session['destinyMembershipId'], loadout)
    except destiny.DestinyException as e:
        #TODO trace this error Finding process can Transfer or NotFound or a Equip (locked) may not catch inners
        flash(str(e) ,'danger')
    #finally:
    #    flash('Loadout Equipped', 'message')
    return redirect(url_for('dashboard'))



@app.route('/loadout/delete', methods=["POST"])
@login_required
def deleteLoadout():
    id = request.form.get("loadoutid")
    a = db.session.query(models.Loadout).filter_by(id=id).first()
    db.session.delete(a)
    db.session.commit()
    flash("Loadout Deleted.", 'danger')
    return redirect(url_for("dashboard"))


@app.route('/reload', methods=["POST"])
def reload():
    requests_cache.clear()
    session.clear()
    return redirect(request.referrer)


'''
Jinja2 Filters: |json didn't work
'''


def getjson(string):
    return json.loads(string)


app.jinja_env.filters['getjson'] = getjson


'''
Testing Routes: Tool for manually running API calls/Debugging. Removed in Production
'''





'''
Create Logging session on gunicorn Server
'''


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


if __name__ == "__main__":
    app.run(ssl_context='adhoc')
    #runs the app in Dev
    #wsgi.py is "__main__" in prod