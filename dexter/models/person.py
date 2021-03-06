# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta
import logging

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    )
from sqlalchemy.orm import relationship, subqueryload
from wtforms import StringField, validators, SelectField, HiddenField

from .support import db
from ..forms import Form, MultiCheckboxField

class Person(db.Model):
    """
    A person, with a bit more info than just the 'person' entity. Multiple 'person' entities
    can link to a single person.
    """
    __tablename__ = "people"

    log = logging.getLogger(__name__)

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), index=True, nullable=False, unique=True)
    gender_id   = Column(Integer, ForeignKey('genders.id'))
    race_id     = Column(Integer, ForeignKey('races.id'))
    affiliation_id = Column(Integer, ForeignKey('affiliations.id'))

    created_at   = Column(DateTime(timezone=True), index=True, unique=False, nullable=False, server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    # Associations
    gender      = relationship("Gender", lazy=False)
    race        = relationship("Race", lazy=False)
    affiliation = relationship("Affiliation")

    def entity(self):
        """ Get an entity that is linked to this person. Because many entities can be linked, we
        try find the one with an exact name match before just returning any old one. """
        from . import Entity

        last = None

        # get all the entities and try to find the one that has an exact
        # name match
        for e in self.entities:
            last = e
            if e.name == self.name:
                return e

        # no exact match, just return the last one
        return last

    def get_alias_entity_ids(self):
        """
        Return a list of entity ids that are aliases for this person.
        """
        return [e.id for e in self.entities]

    def set_alias_entity_ids(self, ids):
        """
        Updated entities linked to this person by setting a list of
        entity ids.
        """
        from . import Entity
        self.entities = Entity.query.filter(Entity.id.in_(ids)).all()

    alias_entity_ids = property(get_alias_entity_ids, set_alias_entity_ids)


    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'race': self.race.name if self.race else None,
            'gender': self.gender.name if self.gender else None,
            'affiliation': self.affiliation.full_name() if self.affiliation else None,
        }


    def relearn_affiliation(self):
        """ Relearn this person's affiliation, based on a time-decaying
        weighted average of affiliation mappings taken from document
        sources. 
        
        We consider all changes that have taken place over the last 7
        days. The current affiliation (if any), is considered to have
        been set exactly 7 days ago.

        All dates are based on document publication dates.

        Returns True if the affiliation was updated, False otherwise.
        """
        from . import DocumentSource, Document

        now = datetime.utcnow()
        days_ago = now - timedelta(days=7)

        sources = DocumentSource.query\
                .options(subqueryload(DocumentSource.document))\
                .options(subqueryload(DocumentSource.affiliation))\
                .filter(Document.published_at >= days_ago)\
                .filter(DocumentSource.person == self)\
                .filter(DocumentSource.affiliation != None)\
                .order_by(Document.published_at)\
                .all()

        weights = {}

        # exponential decay. An affiliation from today is worth
        # only half that tomorrow, a half again the day after, etc.
        weight = lambda d: 1.0 / (2 ** (now - d).days)

        # current affiliation
        if self.affiliation:
            weights[self.affiliation] = weight(days_ago)

        # accumulate weights for affiliations gathered over the last
        # period
        for source in sources:
            weights[source.affiliation] = \
                    weights.get(source.affiliation, 0) + \
                    weight(source.document.published_at)

        self.log.debug("Affiliation weights for %s: %s" % (self, weights))

        if weights:
            affiliation, _ = max(weights.items(), key=lambda pair: pair[1])

            if affiliation != self.affiliation:
                self.log.info("Learned new affiliation for %s: was=%s, now=%s" % (self, self.affiliation, affiliation))
                self.affiliation = affiliation
                return True

        return False


    def __repr__(self):
        return "<Person id=%s, name=\"%s\">" % (self.id, self.name.encode('utf-8'))

    @classmethod
    def get_or_create(cls, name, gender=None, race=None):
        from . import Entity

        p = Person.query.filter(Person.name == name).first()
        if not p:
            p = Person()
            p.name = name

            if gender:
                p.gender = gender
            if race:
                p.race = race

            # link entities that are similar
            for e in Entity.query.filter(Entity.name == name, Entity.group == 'person', Entity.person == None).all():
                e.person = p

            db.session.add(p)
            # force a db write (within the transaction) so subsequent lookups
            # find this entity
            db.session.flush()
        return p


class PersonForm(Form):
    gender_id  = SelectField('Gender', default='')
    race_id    = SelectField('Race', default='')
    alias_entity_ids = MultiCheckboxField('Aliases')

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)

        from . import Entity

        self.gender_id.choices = [['', '(unknown gender)']] + [[str(g.id), g.name] for g in Gender.query.order_by(Gender.name).all()]
        self.race_id.choices = [['', '(unknown race)']] + [[str(r.id), r.name] for r in Race.query.order_by(Race.name).all()]

        # we don't care if the entities are in the valid list or not
        self.alias_entity_ids.pre_validate = lambda form: True


class Gender(db.Model):
    __tablename__ = "genders"

    id        = Column(Integer, primary_key=True)
    name      = Column(String(150), index=True, nullable=False, unique=True)

    def __repr__(self):
        return "<Gender name='%s'>" % (self.name)

    def abbr(self):
        return self.name[0].upper()

    @classmethod
    def male(cls):
        return Gender.query.filter(Gender.name == 'Male').one()

    @classmethod
    def female(cls):
        return Gender.query.filter(Gender.name == 'Female').one()

    @classmethod
    def create_defaults(cls):
        text = """
        Female
        Male
        Other: Transgender, Transsexual
        """
        genders = []
        for s in text.strip().split("\n"):
            g = Gender()
            g.name = s.strip()
            genders.append(g)

        return genders


class Race(db.Model):
    __tablename__ = "races"

    id        = Column(Integer, primary_key=True)
    name      = Column(String(50), index=True, nullable=False, unique=True)

    def __repr__(self):
        return "<Race name='%s'>" % (self.name)

    def abbr(self):
        return self.name[0].upper()

    @classmethod
    def create_defaults(self):
        text = """
        Black
        White
        Coloured
        Asian
        Indian
        Other
        """

        races = []
        for s in text.strip().split("\n"):
            g = Race()
            g.name = s.strip()
            races.append(g)

        return races
