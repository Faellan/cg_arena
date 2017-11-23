# Parce que dès qu'on a le choix, python > all
EXE_DIRECTORY = './ARENA/real_exe/'
# OUTPUT_DIRECTORY = './ARENA/output/'
REFEREE_JAR = './cg-mm.jar'
NUMBER_OF_ROUNDS = 200
RANDOM_MATCHING_OFFSET = 50

######################

import os
import time
from glob import glob
from itertools import zip_longest, product
from elo import rate_1vs1
from random import randint
from subprocess import Popen, PIPE, STDOUT

def read_line(process, preformat=True):
    line_in_bytes = process.stdout.readline()
    line_in_str = line_in_bytes.decode()
    line_in_cleaned_str = line_in_str.replace('\n', '')
    if preformat:
        list_of_str = line_in_cleaned_str.split()
        res = []
        for v in list_of_str:
            try:
                res.append(int(v))
            except ValueError:
                try:
                    res.append(float(v))
                except ValueError:
                    res.append(v)
        return res
    else:
        if line_in_cleaned_str == "null":
            return read_line(process, preformat)
        return line_in_cleaned_str

def read_lines(process, number_of_lines):
    return [read_line(process) for i in range(number_of_lines)]

def send_line(process, line):
    str_line = ' '.join([str(v) for v in line]) + '\n'
    encoded_line = str.encode(str_line)
    process.stdin.write(encoded_line)
    process.stdin.flush()

def send_lines(process, lines):
    for line in lines:
        send_line(process, line)

def line_type(line):
    # print(line)
    assert line.startswith('###')
    first_part = line.split()[0]
    return first_part[3:]

def get_input_for_turn(process):
    scores_rage = read_lines(process, 6)
    number_of_units = read_line(process)
    units = read_lines(process, number_of_units[0])
    input_for_turn = [*scores_rage, number_of_units, *units]
    return input_for_turn

class Program:
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = os.path.splitext(
            os.path.basename(file_path))[0]
        self.elo = 1200

    def start_process(self):
        return Popen(
            [self.file_path],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )

class Match:

    def __init__(self, round_number, programs):
        assert len(programs) == 3
        self.round_number = round_number
        self.players = [{
            'program': program,
            'score': 0,
            'new_elos': [],
        } for program in programs]

    def run(self):
        self.describe()
        self.perform_match()
        self.rate_players()
        self.print_results()

    def describe(self):
        print(' [match]')
        for player in self.players:
            print('   -> {} : {}'.format(player['program'].name, player['program'].elo))

    def perform_match(self):
        
        referee_process = Popen(
            ['/usr/bin/java', '-jar', REFEREE_JAR],
            stdout=PIPE, stdin=PIPE, stderr=PIPE)
        time.sleep(1)
        poll = referee_process.poll()
        if poll == None:
            print('Referee started')
        else:
            raise RuntimeError('Referee failed :/')
        players_process = [player['program'].start_process() for player in self.players]

        send_line(referee_process, [0])

        input_for_turn = []
        
        game_over = False
        next_player_id = 0

        while not game_over:

            line = read_line(referee_process, False)

            if line_type(line) == 'End':
                scores = line.split()[1:]
                assert len(scores) == 3
                for player, score in zip(self.players, scores):
                    player['score'] = score
                game_over = True

            elif line_type(line) == 'Input':
                input_for_turn = get_input_for_turn(referee_process)

            elif line_type(line) == 'Output':
                send_lines(players_process[next_player_id], input_for_turn)
                orders_by_player = read_lines(players_process[next_player_id], 3)
                send_lines(referee_process, orders_by_player)
                next_player_id = (next_player_id + 1) % 3

            else:
                raise RuntimeError('Unexpected line {}'.format(line))

        referee_process.terminate()

        for player_process in players_process:
            player_process.terminate()

    def rate_players(self):
        for p1, p2 in product(self.players, self.players):
            if p1 == p2: continue
            if p1['score'] > p2['score']:
                new_elo_p1, new_elo_p2 = rate_1vs1(p1['program'].elo, p2['program'].elo)
            elif p2['score'] > p1['score']:
                new_elo_p2, new_elo_p1 = rate_1vs1(p2['program'].elo, p1['program'].elo)
            else:
                new_elo_p1, new_elo_p2 = rate_1vs1(
                    p1['program'].elo, 
                    p2['program'].elo,
                    drawn=True)
            p1['new_elos'].append(new_elo_p1)
            p2['new_elos'].append(new_elo_p2)

        for player in self.players:
            player['program'].elo = sum(player['new_elos'])/len(player['new_elos'])

    def print_results(self):

        print(' (results) :')
        for player in self.players:
            print('    -> {} : {} ({})'.format(
                player['program'].name, 
                player['score'],
                player['program'].elo,
            ))


class Arena:

    def __init__(self):
        self.programs = []

    def run(self):
        assert len(self.programs) % 3 == 0

        for round_number in range(NUMBER_OF_ROUNDS):
            print('[STARTING ROUND {}]'.format(round_number))

            self.show_rankings()

            sorted_programs = sorted(
                self.programs, 
                key=lambda p: p.elo + randint(
                    -RANDOM_MATCHING_OFFSET,
                    RANDOM_MATCHING_OFFSET),
                reverse=True,
            )

            block = [iter(sorted_programs)] * 3
            round_matches = [
                Match(
                    round_number=round_number,
                    programs=programs,
                ) for programs in zip_longest(*block)]

            print('{} matches for this round'.format(len(round_matches)))

            for match in round_matches:
                print('[starting match]')
                match.run()

            print('[ENDING ROUND {}]\n\n\n\n'.format(round_number))
            time.sleep(1)

    def show_rankings(self):
        sorted_programs = sorted(
            self.programs, 
            key=lambda p: p.elo,
            reverse=True,
        )

        for rank, program in enumerate(sorted_programs):
            print(' {}. {} {}'.format(rank+1, program.elo, program.name))

arena = Arena()

for file_path in glob(os.path.join(EXE_DIRECTORY, '*.exe')):
    arena.programs.append(Program(file_path))

arena.run()