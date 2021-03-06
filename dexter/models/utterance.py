from __future__ import division

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
    Index
    )
from sqlalchemy.orm import relationship, backref
import nltk

from .support import db

class Utterance(db.Model):
    """
    A quotation by an entity in a document.

    Two instances are equal if they are from the same entity and have the same
    quotation.
    """
    __tablename__ = "utterances"

    id        = Column(Integer, primary_key=True)
    doc_id    = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), index=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), index=True)
    quote     = Column(Text, nullable=False)

    created_at   = Column(DateTime(timezone=True), index=True, unique=False, nullable=False, server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    # Associations
    entity    = relationship("Entity", lazy=False)

    # offset and length of quotation in the document
    offset    = Column(Integer)
    length    = Column(Integer)


    def similarity(self, other):
        """
        Return a similarity ratio of two quotes. 0 means the strings are not similar at all,
        1.0 means they're identical. This is the Levenshtein ratio:

          (lensum - ldist) / lensum

        where lensum is the sum of the length of the two strings and ldist is the
        Levenshtein distance (edit distance).

        See https://groups.google.com/forum/#!topic/nltk-users/u94RFDWbGyw
        """
        lensum = len(self.quote) + len(other.quote)
        ldist = nltk.edit_distance(self.quote, other.quote)

        if lensum == 0:
            return 0

        return (lensum - ldist) / lensum


    def __eq__(self, other):
        return isinstance(other, Utterance) and other.entity == self.entity and \
                (other.quote.lower() == self.quote.lower() or self.similarity(other) >= 0.8)

    def __repr__(self):
        return "<Utterance doc=%s, entity=%s, quote=\"%s\">" % (
                self.document, self.entity, (self.quote or "").encode('utf-8')[0:15] + "...")
