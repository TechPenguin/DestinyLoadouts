from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    membershipId = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.membershipId


class Loadout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    characterid = db.Column(db.Integer, nullable=False)
    loadout = db.Column(db.Text, nullable=False)

    def __init__(self, userid,characterid,loadout):
        self.userid = userid
        self.characterid = characterid
        self.loadout = loadout

    def __repr__(self):
        return '<Loadout %r>' % self.id
