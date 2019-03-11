"""sqlalchemy models"""
# pylint: disable=too-few-public-methods,abstract-method

from datetime import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship

from sner.server import db


class Host(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	address = db.Column(postgresql.INET, nullable=False)
	hostname = db.Column(db.String(256))
	os = db.Column(db.Text)
	created = db.Column(db.DateTime, default=datetime.utcnow)
	modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	services = relationship('Service', back_populates='host', cascade='delete,delete-orphan')
	notes = relationship('Note', back_populates='host', cascade='delete,delete-orphan')

	def __repr__(self):
		return '%s (%s)' % (self.address, self.hostname if self.hostname else '')


class Service(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	host_id = db.Column(db.Integer, db.ForeignKey('host.id'))
	proto = db.Column(db.String(10), nullable=False)
	port = db.Column(db.Integer, nullable=False)
	state = db.Column(db.String(100))
	name = db.Column(db.String(100))
	info = db.Column(db.String(2000))
	created = db.Column(db.DateTime, default=datetime.utcnow)
	modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	host = relationship('Host', back_populates='services')


class Note(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	host_id = db.Column(db.Integer, db.ForeignKey('host.id'))
	ntype = db.Column(db.String(500))
	data = db.Column(db.Text)
	created = db.Column(db.DateTime, default=datetime.utcnow)
	modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	host = relationship('Host', back_populates='notes')
