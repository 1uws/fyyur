from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

Venue_genre = db.Table('Venue_genre',
	db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
	db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

Artist_genre = db.Table('Artist_genre',
	db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
	db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Venue(db.Model):
	__tablename__ = 'Venue'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	address = db.Column(db.String(120))
	phone = db.Column(db.String(120))
	image_link = db.Column(db.String(500))
	facebook_link = db.Column(db.String(120))
	genres = db.relationship('Genre', secondary=Venue_genre, backref=db.backref('venues'))
	city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
	website = db.Column(db.String(120))
	seeking_talent = db.Column(db.Boolean, nullable=False)
	seeking_description = db.Column(db.String)
	shows = db.relationship('Show', backref='venue')

class Artist(db.Model):
	__tablename__ = 'Artist'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	phone = db.Column(db.String(120))
	image_link = db.Column(db.String(500))
	facebook_link = db.Column(db.String(120))
	city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
	genres = db.relationship('Genre', secondary=Artist_genre, backref=db.backref('artists'))
	website = db.Column(db.String(120))
	seeking_venue = db.Column(db.Boolean, nullable=False)
	seeking_description = db.Column(db.String)
	shows = db.relationship('Show', backref='artist')

class City(db.Model):
	__tablename__ = 'City'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), nullable=False)
	state = db.Column(db.String(120))
	artists = db.relationship('Artist', backref='city')
	venues = db.relationship('Venue', backref='city')

class Genre(db.Model):
	__tablename__ = 'Genre'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), nullable=False)

class Show(db.Model):
	__tablename__ = 'Show'

	id = db.Column(db.Integer, primary_key=True)
	start_time = db.Column(db.String(50))
	venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
	artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)