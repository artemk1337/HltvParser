
from bs4 import BeautifulSoup
from lxml import html
import datetime as dt
import pandas as pd
import requests


# https://www.hltv.org/results?offset=0
# https://www.hltv.org/results?offset=100
PREFIX = "https://www.hltv.org/"
DATE_FORMAT = '%Y-%m-%d'


# parse page and create BeautifulSoup
def parse_page(url: str) -> BeautifulSoup:
	page = requests.get(url)
	if page.status_code != 200:
		print(f"Can't load page {url}")
	return BeautifulSoup(page.text, 'html.parser')


# get N matches from result pages
def get_all_mathes(n_last_matches: int) -> list:
	matches = []
	url_prefix = 'https://www.hltv.org/results?offset='
	c_match_page = 100
	## ETOT KOD HUINYA
	# for page_postfix in range(n_last_matches // c_match_page + 1):
	# 	url = url_prefix + str(page_postfix * 100)
	# 	parsed_info = parse_page(url)
	# 	sublists = parsed_info.find_all('div', {'class': 'results-holder allres'})[0]\
	# 		.find_all('div', {'class': 'results-sublist'})
	# 	for sublist in sublists:
	# 		for match in sublist.find_all('div', {'class': 'result-con'}):
	# 			matches += [match.find_all('a', {'class': 'a-reset'})[0].get('href')]
	return [match.find_all('a', {'class': 'a-reset'})[0].get('href') \
				for page_postfix in range	(n_last_matches // c_match_page + 1) \
				for sublist in parse_page (url_prefix + str(page_postfix * 100)).find_all('div', {'class': 'results-holder allres'})[0]\
				.find_all('div', {'class': 'results-sublist'}) \
				for match in sublist.find_all('div', {'class': 'result-con'})][:n_last_matches]


# https://www.hltv.org/matches/2353120/dbl-poney-vs-unique-pinnacle-fall-series-3


# get all team rank
def get_match_ranks(match_page: BeautifulSoup) -> [str, str]:
	ranks = []
	lineups = match_page.find_all('div', {'class': 'lineups'})
	for lineup in lineups:
		rankes_p = lineup.find_all('div', {'class': 'teamRanking'})
		for rank_p in rankes_p:
			# rank = rank_p.find('a').text.split('#')[-1]
			rank = rank_p.find('a').text
			ranks += [rank]
	return ranks


# def get_score_match(match_url: str) -> (int, int):
# 	pass


# get results for each team 
def get_match_results(match_page: BeautifulSoup) -> dict:
	"""
	:return:
		dict; example: {'inferno': [16, 2], 'mirage': [7, 16]}
	"""
	won_matches  = match_page.find_all('div', {'class': "won"})[0].text 
	lost_matches  = match_page.find_all('div', {'class': "lost"})[0].text 

	match_results_output = dict()

	# div class mapholder
	for map_holder in match_page.find_all('div', {'class': "mapholder"})[:int(won_matches) + int(lost_matches)]:
		current_map = map_holder.find_all("div", {"class" :"mapname"})[0].text
		match_results_output[current_map] = list()
		for played_results in map_holder.find_all("div", {"class":"results played"}):
			for match_results in played_results.find_all('div', {"class": "results-team-score"}):
				match_results_output[current_map].append(match_results.text)
	return match_results_output



def get_match_date(match_page: BeautifulSoup) -> int:
	unixtime = match_page.find_all('div', {'class': 'date'})[0].get('data-unix')
	# print(dt.datetime.utcfromtimestamp(int(unixtime[:-3])).strftime('%Y-%m-%d %H:%M:%S'))
	# dt.datetime.utcfromtimestamp(time).strftime('%Y-%m-%d) - timedelta(days=1)
	# dt.datetime.utcfromtimestamp(time).strftime('%Y-%m-%d) - timedelta(days=91)
	return int(unixtime[:-3])


def get_teams_ident_match(match_page: BeautifulSoup) -> [str, str]:
	return [team.find('a').get('href').split('team/')[-1] 
			for team in match_page.find_all('div', {'class': 'team'})]


def get_winstreak_match(match_page: BeautifulSoup) -> [int, int]:
	winstreaks = []
	for data_ in match_page.find_all("div", {"class": "past-matches-grid"})[0]. \
		find_all("div", { "class": "past-matches-headline"}):
		# team_name = [val.text for val in data_.find_all("div", {"class": "past-matches-teamname text-ellipsis"})]
		try:
			winstreaks += [(int([val.text for val in data_.find_all("div", {"class" : "past-matches-streak"})][0].split(' ')[0]))]
		except:
			winstreaks += [0]
	return winstreaks


# https://www.hltv.org/stats/teams/maps/11003/dbl-poney?startDate=2021-08-24&endDate=2021-11-24
# https://www.hltv.org/stats/teams/maps/11003/dbl-poney?startDate=2021-08-24&endDate=2021-11-24

def get_stat_team_page(team_ident: str, start_time_unix: str, end_date_unix: str) -> BeautifulSoup:
	url = PREFIX + 'stats/teams/maps/' + team_ident + f'?startDate={start_time_unix}&endDate={end_date_unix}'
	print("URL: ", url)
	return parse_page(url)
	

# get team staticstics for one map
def get_team_stat_map(stat_page: BeautifulSoup, map: str, stats_name: list) -> dict:
	output_data = {key: None for key in stats_name}
	
	try:
		col_maps = stat_page.find('div', {'class': 'two-grid'})
		
		for col_map in col_maps.find_all('div', {'class': 'col'}, recursive=False):
			map_name = col_map.find('div', {'class': 'map-pool-map-name'}).text
			if map_name != map:
				continue
			for stat_row, stat_name in zip(col_map.find_all('div', {"class": "stats-row"}), stats_name):
				stat_result = stat_row.find_all('span')[-1].text
				output_data[stat_name] = stat_result
	except:
		pass
	return output_data


def get_match_stat_df(match_url: str):
	df = None

	match_page = parse_page(match_url)

	match_result = get_match_results(match_page)
	print("Match Score by maps: ",  ' | '.join(match_result))
	
	match_ranks = get_match_ranks(match_page)
	print("Match Ranks: ", match_ranks)

	win_streaks_for_match = [str(i) for i in get_winstreak_match(match_page)]
	print("Winsteak of teams: " ,  ' | '.join(win_streaks_for_match))
	
	team_idents = get_teams_ident_match(match_page)
	print("Each teams identificators:", ' | '.join(team_idents))
	
	unix_time = get_match_date(match_page)
	print("Match Date in unix time: ", unix_time)
	
	team1_stat_page, team2_stat_page = [get_stat_team_page(team_ident, 
						end_date_unix=(dt.datetime.utcfromtimestamp(unix_time) - dt.timedelta(days=1)).strftime(DATE_FORMAT),
						start_time_unix=(dt.datetime.utcfromtimestamp(unix_time) - dt.timedelta(days=91)).strftime(DATE_FORMAT)) for team_ident in team_idents]

	stats_name = ['w/d/l', 'win_rate', 'total_rounds', 'r_win_after_first_kill', 'r_win_after_first_death']
	for map_, _ in match_result.items():
		stat_team1 = get_team_stat_map(team1_stat_page, map_, stats_name)
		print(f"Stat for team1 map {map_}: \n {stat_team1}")
		
		stat_team2 = get_team_stat_map(team2_stat_page, map_, stats_name)
		print(f"Stat for team2 map {map_}: \n {stat_team2}")

		cols = ['time', 'url', 
				'ident_team1', 'ident_team2', 
				'score_map_team1', 'score_map_team2', 
				'rank_team1', 'rank_team2',
				'winstreak_team1', 'winstreak_team2', 
				*[stat_name + '_team1' for stat_name in stats_name], 
				*[stat_name + '_team2' for stat_name in stats_name]]
		data = [[unix_time, match_url, *team_idents, *match_result[map_], *match_ranks, *win_streaks_for_match, 
		*list(stat_team1.values()), *list(stat_team2.values())]]
		df = df.append(pd.DataFrame(data=data, columns=cols)) if df is not None else pd.DataFrame(data=data, columns=cols)

	return df


if __name__ == "__main__":
	df = None
	matches = get_all_mathes(30)
	for match in matches:
		get_match_stat_df(PREFIX + match)
		