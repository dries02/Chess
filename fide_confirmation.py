import pandas as pd
import requests
import math
from bs4 import BeautifulSoup

# Rename these constants based on the spreadsheet layout.
PARTICIPANTS_FILENAME = 'artificial_fide_confirmation.xlsx'
FIRSTNAME_COLNAME = 'First name'
SURNAME_COLNAME = 'Last name'
RATING_COLNAME = 'FIDE rating'
ID_COLNAME = 'FIDE ID'
TITLE_COLNAME = 'FIDE title'
FIDE_WEBPAGE = 'https://ratings.fide.com/profile/'
LOGGER_FILENAME = 'logger.txt'


class Player:
	"""
	Represents the player as indicated in the spreadsheet.
	"""
	def __init__(self, first_name, surname, rating, fide_id, title):
		self.__name = surname + ', ' + first_name
		self.__rating = rating
		self.__fide_id = fide_id
		self.__title = title

	def get_id(self):
		return str(self.__fide_id)

	def get_name(self):
		return self.__name

	def get_rating(self):
		return str(self.__rating)

	def get_title(self):
		return self.__title


def retrieve_true_attributes(response):
	"""
	Scrapes the player name, rating, and title.
	:param response: the response object associated with the URL of the player's FIDE page.
	:return: a triplet of the player's true name, rating, and title.
	"""
	soup = BeautifulSoup(response.text, 'html.parser')
	true_name = soup.title.text
	true_rating = soup.find("div", class_="profile-top-rating-data profile-top-rating-data_gray").contents[
		-1].text.strip()
	true_title = soup.find("div", class_="profile-top-info__block__row__header", string="FIDE title:").\
		find_next_sibling("div", class_="profile-top-info__block__row__data").text
	# Treat a 'None' title as a missing title. This depends on how it is represented in the spreadsheet.
	if true_title == 'None':
		true_title = float('nan')
	return true_name, true_rating, true_title


def is_missing_title(title):
	# Keep in mind that generally nan != nan
	return isinstance(title, float) and math.isnan(title)


def verify_player(player, f):
	"""
	Verifies the player's name, rating, title. Any issues are reported to the output file.
	:param player: the player to check.
	:param f: the output file to write issues to.
	"""
	url = FIDE_WEBPAGE + player.get_id()
	response = requests.get(url)
	if not response.ok:
		f.write(
			f'{player.get_name()} reported {player.get_id()} as their ID, but this could not be retrieved. '
			f'Error code = {response.status_code}\n'
		)
		return
	mistake_flag = False
	true_name, true_rating, true_title = retrieve_true_attributes(response)
	if player.get_name().lower() != true_name.lower():
		f.write(f'Player says their name is {player.get_name()}, but FIDE says {true_name}\n')
		mistake_flag = True
	if player.get_rating() != true_rating:
		f.write(f'{player.get_name()} reported {player.get_rating()} as their rating, but FIDE says {true_rating}\n')
		mistake_flag = True
	if player.get_title() != true_title and is_missing_title(player.get_title()) is not is_missing_title(true_title):
		f.write(f'{player.get_name()} reported {player.get_title()} as their title, but FIDE says {true_title}\n')
		mistake_flag = True
	if not mistake_flag:
		print(f'{player.get_name()} reported everything correctly!')


def main():
	participants_df = pd.read_excel(PARTICIPANTS_FILENAME)
	# There might be a better way to do this but this looks rather straightforward :)
	# https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
	with open(LOGGER_FILENAME, 'w') as f:
		for i in participants_df.index:
			current_player = Player(
				participants_df[FIRSTNAME_COLNAME][i],
				participants_df[SURNAME_COLNAME][i],
				participants_df[RATING_COLNAME][i],
				participants_df[ID_COLNAME][i],
				participants_df[TITLE_COLNAME][i],
			)
			verify_player(current_player, f)


if __name__ == '__main__':
	main()
