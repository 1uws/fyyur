#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
import sys

from models import Venue, Artist, City, Genre, Show, db

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime_from_raw(date, format='medium'):
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Utils.
#----------------------------------------------------------------------------#

def db_add_genre(new_genres):
	current_genres = Genre.query.filter(Genre.name.in_(new_genres)).all()
	genres = []
	for genre_name in new_genres:
		try:
			index = [x.name for x in current_genres].index(genre_name)
		except ValueError:
			index = None
		if index is None:
			new_genre = Genre(name = genre_name)
			db.session.add(new_genre)
			genres.append(new_genre)
		else:
			genres.append(current_genres[index])
	return genres

def db_add_city(new_city, new_state):
	city = City.query.filter(City.name == new_city, City.state == new_state).first()
	if city is None:
		city = City(name = new_city, state = new_state)
		db.session.add(city)
	return city

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
	return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
	venues = Venue.query.all()
	cities = City.query.all()
	data = []
	for city in cities:
		city_venues = []
		for venue in venues:
			if city.id == venue.city_id:
				city_venues.append(venue)
		if 0!=len(city_venues):
			data.append({
				'city': city.name,
				'state': city.state,
				'venues': city_venues
			})
	return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
	data = []
	search_term = request.form.get('search_term', '')
	venues = Venue.query.all()
	for venue in venues:
		if search_term.lower() in venue.name.lower():
			data.append({
				'id': venue.id,
				'name': venue.name
			})
	response = {
		'count': len(data),
		'data': data
	}
	return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
	venue = Venue.query.get(venue_id)
	city = City.query.get(venue.city_id)
	shows = venue.shows

	past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.today()).all()
	past_shows = []
	for show in past_shows_query:
		venue = Venue.query.get(show.venue_id)
		new_show = {
			'venue_id': show.venue_id,
			'venue_name': venue.name,
			'venue_image_link': venue.image_link,
			'start_time': format_datetime_from_raw(show.start_time),
		}
		past_shows.append(new_show)

	upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>=datetime.today()).all()
	upcoming_shows = []
	for show in upcoming_shows_query:
		venue = Venue.query.get(show.venue_id)
		new_show = {
			'venue_id': show.venue_id,
			'venue_name': venue.name,
			'venue_image_link': venue.image_link,
			'start_time': format_datetime_from_raw(show.start_time),
		}
		upcoming_shows.append(new_show)

	data = {
		'name': venue.name,
		'id': venue.id,
		'address': venue.address,
		'city': city.name,
		'state': city.state,
		'genres': [x.name for x in venue.genres],
		'phone': venue.phone,
		'website': venue.website,
		'facebook_link': venue.facebook_link,
		'image_link': venue.image_link,
		'seeking_talent': venue.seeking_talent,
		'seeking_description': venue.seeking_description,
		'past_shows_count': len(past_shows),
		'past_shows': past_shows,
		'upcoming_shows_count': len(upcoming_shows),
		'upcoming_shows': upcoming_shows,
	}
	return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
	form = VenueForm(request.form)
	if not form.validate():
		for n,e in form.errors.items():
			flash(e[0])
			break
		return render_template('forms/new_venue.html', form=form)
	try:
		genres = db_add_genre(request.form.getlist('genres'))
		city = db_add_city(request.form['city'], request.form['state'])
		db.session.flush()

		venue = Venue(
			name = request.form['name'],
			address = request.form['address'],
			phone = request.form['phone'],
			city_id = city.id,
			image_link = request.form['image_link'],
			facebook_link = request.form['facebook_link'],
			website = request.form['website_link'],
			seeking_talent = request.form.get('seeking_talent', '') == 'y',
			seeking_description = request.form['seeking_description'],
		)

		for genre in genres:
			venue.genres.append(genre)

		db.session.add(venue)
		db.session.commit()
		flash('Venue ' + request.form['name'] + ' was successfully listed!')
	except:
		db.session.rollback()
		print(sys.exc_info())
		flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
	finally:
		db.session.close()

	return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
	data = Artist.query.all()
	return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
	search_term = request.form.get('search_term', '')
	artists = Artist.query.all()

	data = [{
		'id': artist.id,
		'name': artist.name
	} for artist in artists if search_term.lower() in artist.name.lower()]

	response = {
		'count': len(data),
		'data': data
	}
	return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
	artist = Artist.query.get(artist_id)
	city = City.query.get(artist.city_id)
	shows = artist.shows

	past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.today()).all()
	past_shows = []
	for show in past_shows_query:
		venue = Venue.query.get(show.venue_id)
		new_show = {
			'venue_id': show.venue_id,
			'venue_name': venue.name,
			'venue_image_link': venue.image_link,
			'start_time': format_datetime_from_raw(show.start_time),
		}
		past_shows.append(new_show)

	upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>=datetime.today()).all()
	upcoming_shows = []
	for show in upcoming_shows_query:
		venue = Venue.query.get(show.venue_id)
		new_show = {
			'venue_id': show.venue_id,
			'venue_name': venue.name,
			'venue_image_link': venue.image_link,
			'start_time': format_datetime_from_raw(show.start_time),
		}
		upcoming_shows.append(new_show)

	data = {
		'name': artist.name,
		'id': artist.id,
		'city': city.name,
		'state': city.state,
		'genres': [x.name for x in artist.genres],
		'phone': artist.phone,
		'website': artist.website,
		'facebook_link': artist.facebook_link,
		'image_link': artist.image_link,
		'seeking_venue': artist.seeking_venue,
		'seeking_description': artist.seeking_description,
		'past_shows_count': len(past_shows),
		'past_shows': past_shows,
		'upcoming_shows_count': len(upcoming_shows),
		'upcoming_shows': upcoming_shows,
	}

	return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
	form = ArtistForm()
	artist = Artist.query.get(artist_id)
	city = City.query.get(artist.city_id)
	artist = {
		'id': artist.id,
		'name': artist.name,
		'genres': [x.name for x in artist.genres],
		'city': city.name,
		'state': city.state,
		'phone': artist.phone,
		'website': artist.website,
		'facebook_link': artist.facebook_link,
		'seeking_venue': artist.seeking_venue,
		'seeking_description': artist.seeking_description,
		'image_link': artist.image_link,
	}
	form.name.data = artist['name']
	form.genres.data = artist['genres']
	form.city.data = artist['city']
	form.state.data = artist['state']
	form.phone.data = artist['phone']
	form.website_link.data = artist['website']
	form.facebook_link.data = artist['facebook_link']
	form.image_link.data = artist['image_link']
	form.seeking_venue.data = artist['seeking_venue']
	form.seeking_description.data = artist['seeking_description']
	return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
	form = ArtistForm(request.form)
	if not form.validate():
		for n,e in form.errors.items():
			flash(e[0])
			break
		return redirect(url_for('edit_artist', artist_id=artist_id))
	try:
		genres = db_add_genre(request.form.getlist('genres'))
		city = db_add_city(request.form['city'], request.form['state'])
		db.session.flush()

		artist = Artist.query.get(artist_id)
		artist.name = request.form['name']
		artist.city_id = city.id
		artist.phone = request.form['phone']
		artist.website = request.form['website_link']
		artist.facebook_link = request.form['facebook_link']
		artist.seeking_venue = request.form.get('seeking_venue', '') == 'y'
		artist.seeking_description = request.form['seeking_description']
		artist.image_link = request.form['image_link']

		artist.genres = []
		for genre in genres:
			artist.genres.append(genre)

		db.session.commit()
	except:
		db.session.rollback()
		print(sys.exc_info())
	finally:
		db.session.close()
	return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
	form = VenueForm()
	venue = Venue.query.get(venue_id)
	city = City.query.get(venue.city_id)
	venue = {
		'id': venue.id,
		'name': venue.name,
		'genres': [x.name for x in venue.genres],
		'address': venue.address,
		'city': city.name,
		'state': city.state,
		'phone': venue.phone,
		'website': venue.website,
		'facebook_link': venue.facebook_link,
		'seeking_talent': venue.seeking_talent,
		'seeking_description': venue.seeking_description,
		'image_link': venue.image_link,
	}
	form.name.data = venue['name']
	form.genres.data = venue['genres']
	form.address.data = venue['address']
	form.city.data = venue['city']
	form.state.data = venue['state']
	form.phone.data = venue['phone']
	form.website_link.data = venue['website']
	form.facebook_link.data = venue['facebook_link']
	form.image_link.data = venue['image_link']
	form.seeking_talent.data = venue['seeking_talent']
	form.seeking_description.data = venue['seeking_description']
	return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
	form = VenueForm(request.form)
	if not form.validate():
		for n,e in form.errors.items():
			flash(e[0])
			break
		return redirect(url_for('edit_venue', venue_id=venue_id))
	try:
		genres = db_add_genre(request.form.getlist('genres'))
		city = db_add_city(request.form['city'], request.form['state'])
		db.session.flush()

		venue = Venue.query.get(venue_id)
		venue.name = request.form['name']
		venue.address = request.form['address']
		venue.city_id = city.id
		venue.phone = request.form['phone']
		venue.website = request.form['website_link']
		venue.facebook_link = request.form['facebook_link']
		venue.seeking_talent = request.form.get('seeking_talent', '') == 'y'
		venue.seeking_description = request.form['seeking_description']
		venue.image_link = request.form['image_link']

		venue.genres = []
		for genre in genres:
			venue.genres.append(genre)

		db.session.commit()
	except:
		db.session.rollback()
		print(sys.exc_info())
	finally:
		db.session.close()
	return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
	form = ArtistForm(request.form)
	if not form.validate():
		for n,e in form.errors.items():
			flash(e[0])
			break
		return render_template('forms/new_artist.html', form=form)
	try:
		genres = db_add_genre(request.form.getlist('genres'))
		city = db_add_city(request.form['city'], request.form['state'])
		db.session.flush()

		artist = Artist(
			name = request.form['name'],
			phone = request.form['phone'],
			city_id = city.id,
			image_link = request.form['image_link'],
			facebook_link = request.form['facebook_link'],
			website = request.form['website_link'],
			seeking_venue = request.form.get('seeking_venue', '') == 'y',
			seeking_description = request.form['seeking_description'],
		)

		for genre in genres:
			artist.genres.append(genre)

		db.session.add(artist)
		db.session.commit()
		flash('Artist ' + request.form['name'] + ' was successfully listed!')
	except:
		db.session.rollback()
		print(sys.exc_info())
		flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
	finally:
		db.session.close()

	return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
	shows = Show.query.all()
	data=[]
	for show in shows:
		venue = Venue.query.get(show.venue_id)
		artist = Artist.query.get(show.artist_id)
		data.append({
			'venue_id': show.venue_id,
			'venue_name': venue.name if None!=venue else '',
			'artist_id': show.artist_id,
			'artist_name': artist.name if None!=artist else '',
			'artist_image_link': artist.image_link if None!=artist else '',
			'start_time': format_datetime_from_raw(show.start_time)
		})
	return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
	try:
		show = Show(
			artist_id = request.form['artist_id'],
			venue_id = request.form['venue_id'],
			start_time = request.form['start_time'],
		)
		db.session.add(show)
		db.session.commit()
		flash('Show was successfully listed!')
	except:
		db.session.rollback()
		print(sys.exc_info())
		flash('An error occurred. Show could not be listed.')
	finally:
		db.session.close()

	return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
