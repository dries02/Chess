import pandas as pd
import requests
import math
from bs4 import BeautifulSoup
""" From Alice in Wonderland:
"Beautiful Soup, so rich and green,
Waiting in a hot tureen!
Who for such dainties would not stoop?
Soup of the evening, beautiful Soup!"
"""

# TODO Rename these constants based on the spreadsheet layout.
PARTICIPANTS_FILENAME = 'artificial_fide_confirmation.xlsx'
FIRSTNAME_COLNAME = 'First name'
SURNAME_COLNAME = 'Last name'
RATING_COLNAME = 'FIDE rating'
ID_COLNAME = 'FIDE ID'
TITLE_COLNAME = 'FIDE title'
FIDE_WEBPAGE = 'https://ratings.fide.com/profile/'
VERIFICATION_ISSUE_TRACKER_FILENAME = 'verification_issue_tracker.txt'
# TODO map typeform abbreviations to FIDE? Implement in code
ABBREVIATION_TO_TITLE = {
	"GM": "Grandmaster",
	"IM": "International Master",
	"FM": "FIDE Master",
	"CM": "Candidate Master",
	"WGM": "Woman Grandmaster",
	"WIM": "Woman International Master",
	"WFM": "Woman FIDE Master",
	"WCM": "Woman Candidate Master",
	"No title": "None"
}


class Player:
	""" Represents the player as indicated in the spreadsheet. """
	def __init__(self, first_name, surname, rating, fide_id, title):
		self.__name = surname + ', ' + first_name
		self.__rating = str(rating)
		self.__fide_id = str(fide_id)
		self.__title = title

	def get_name(self):
		return self.__name

	def get_rating(self):
		return self.__rating

	def get_fide_id(self):
		return self.__fide_id

	def get_title(self):
		return self.__title


class PlayerVerifier:
	""" Incorporates the verification logic. """
	def __init__(self, player):
		"""
		Constructs a PlayerVerifier.
		:param player: the player to verify.
		"""
		self.__player = player
		self.__found_mistake = False
		self.__fide_soup = None

	def _log_issue(self, reported_player_property, player_property_name, issue):
		"""
		Logs the issue as reported and flags the mistake.
		:param reported_player_property: the player property as reported by the player.
		:param player_property_name: the type of player property.
		:param issue: the description of the problem.
		"""
		issue_description = f'reported {reported_player_property} as their {player_property_name}, but {issue}.'
		log_verification_issue(self.__player.get_name(), issue_description)
		self.__found_mistake = True

	def _retrieve_soup(self):
		"""
		Retrieves the soup associated with the provided FIDE ID.
		:return: True iff the soup was retrieved from FIDE.
		"""
		url = FIDE_WEBPAGE + self.__player.get_fide_id()
		response = requests.get(url)
		if not response.ok:
			self._log_issue(self.__player.get_fide_id(), 'ID', f'this could not be retrieved. Error code = {response.status_code}')
			return False
		self.__fide_soup = BeautifulSoup(response.text, 'html.parser')
		return True

	def _validate_soup(self):
		"""
		Validates the soup associated with the provided FIDE ID.
		:return: True iff there exists a player associated with the FIDE ID.
		"""
		target_div = self.__fide_soup.find('div', class_='row no-gutters').text.strip()
		if target_div == 'No record found please check ID number':
			self._log_issue(self.__player.get_fide_id(), 'ID', 'this is not associated with a player')
			return False
		return True

	def _verify_name(self):
		true_name = self.__fide_soup.title.text
		if self.__player.get_name().lower() != true_name.lower():
			self._log_issue(self.__player.get_name(), 'name', f'FIDE says {true_name}')

	def _verify_rating(self):
		true_rating = self.__fide_soup.find('div', class_='profile-top-rating-data profile-top-rating-data_gray').contents[-1].text.strip()
		if self.__player.get_rating() != true_rating:
			self._log_issue(self.__player.get_rating(), 'rating', f'FIDE says {true_rating}')

	def _verify_title(self):
		true_title = self.__fide_soup.find('div', class_='profile-top-info__block__row__header', string='FIDE title:'). \
			find_next_sibling('div', class_='profile-top-info__block__row__data').text
		# Treat a 'None' title as a missing title. This depends on how it is represented in the spreadsheet.
		if true_title == 'None':
			true_title = float('nan')
		if self.__player.get_title() != true_title and is_missing_title(self.__player.get_title()) != is_missing_title(true_title):
			self._log_issue(self.__player.get_title(), 'title', f'FIDE says {true_title}')

	def _check_found_mistake(self, verbose):
		"""
		Informs the user whether the player has reported their information correctly. Useful for debugging purposes.
		:param verbose: determines whether the debugging information should be printed.
		"""
		if verbose and not self.__found_mistake:
			print(f'{self.__player.get_name()} reported everything correctly!')

	def verify_player(self, verbose=False):
		"""
		Verifies the player's name, rating, title.
		:param verbose: determines whether the debugging information should be printed.
		"""
		if not self._retrieve_soup() or not self._validate_soup():
			return
		self._verify_name()
		self._verify_title()
		self._verify_rating()
		self._check_found_mistake(verbose)


def truncate_file(file_to_truncate):
	"""
	Truncates (empties) the given file. Could also be used to add a header.
	:param file_to_truncate: the file to truncate.
	"""
	with open(file_to_truncate, 'w') as _:
		pass


def log_verification_issue(player_name, issue_description):
	"""
	Logs a verification issue by appending it to the output file.
	:param player_name: the reported name of the player.
	:param issue_description: the description of the issue.
	"""
	with open(VERIFICATION_ISSUE_TRACKER_FILENAME, 'a') as f:
		f.write(f'{player_name}: {issue_description}\n')


def is_missing_title(title):
	# Keep in mind that generally nan != nan
	return isinstance(title, float) and math.isnan(title)


def main():
	truncate_file(VERIFICATION_ISSUE_TRACKER_FILENAME)
	participants_df = pd.read_excel(PARTICIPANTS_FILENAME)
	# There might be a better way to do this but this looks rather straightforward :)
	# https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
	for i in participants_df.index:
		current_player = Player(
			participants_df[FIRSTNAME_COLNAME][i],
			participants_df[SURNAME_COLNAME][i],
			participants_df[RATING_COLNAME][i],
			participants_df[ID_COLNAME][i],
			participants_df[TITLE_COLNAME][i],
		)
		player_verifier = PlayerVerifier(current_player)
		player_verifier.verify_player(verbose=True)


if __name__ == '__main__':
	main()
