import random
import logging
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

RANKS = [-5, -3, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
N_PLAYERS = 6
N_SIMULATIONS = 100000
N_GAMES = 7

def play_turn(hand):
    freq = Counter(hand)
    score = 0
    for rank, count in freq.items():
        score += (count % 2) * rank
    return score

def calculate_best_move(hand, drawn_card):
    current_score = play_turn(hand)
    best_score = current_score
    best_pos = -1

    for i in range(len(hand)):
        temp_hand = hand.copy()
        temp_hand[i] = drawn_card
        new_score = play_turn(temp_hand)
        if new_score < best_score:
            best_score = new_score
            best_pos = i

    return best_pos

def play_game(num_players=6):
    deck = [rank for rank in RANKS for _ in range(4)]
    random.shuffle(deck)

    hands = [[] for _ in range(num_players)]
    for _ in range(8):
        for player in range(num_players):
            hands[player].append(deck.pop())

    draw_pile = deck
    cards_face_up = [0] * num_players
    game_ongoing = True

    while game_ongoing:
        for player in range(num_players):
            if cards_face_up[player] < 8 and draw_pile:
                drawn_card = draw_pile.pop()
                if player == 0:
                    best_pos = calculate_best_move(hands[0], drawn_card)
                    if best_pos != -1:
                        hands[0][best_pos] = drawn_card
                cards_face_up[player] += 1

        if max(cards_face_up) == 8 or not draw_pile:
            game_ongoing = False

    return play_turn(hands[0])

total_matches = 0
round_stats = []

for sim in range(N_SIMULATIONS):
    # Progress bar
    if sim % (N_SIMULATIONS // 100) == 0:
        progress = sim / N_SIMULATIONS * 100
        bar = '=' * int(progress // 2) + '>'
        print(f'\rProgress: [{bar:<50}] {progress:.1f}%', end='', flush=True)

    scores = []
    total_score = 0
    for _ in range(N_GAMES):
        game_score = play_game()
        scores.append(game_score)
        total_score += game_score

    # Check for total score of 6
    if total_score == 6:
        round_stats.append(scores)
        total_matches += 1
        print(f'\nMatch found! Round scores: {scores}')

print(f'\n\nPlay Nine Card Game - Simulation Summary')
print(f'==========================================')
print(f'Simulated {N_SIMULATIONS} games of {N_GAMES} rounds each')
print(f'Looking for games where total score across {N_GAMES} rounds equals 6')
print(f'\nResults:')
print(f'Total matches: {total_matches}')
probability = total_matches/N_SIMULATIONS
print(f'Probability: {probability:.6f} ({probability*100:.4f}%)')
print(f'Approximately 1 in {round(1/probability)} full games')
if round_stats:
    print('\nExample round scores found (each list shows 6 rounds):')
    for i, pattern in enumerate(round_stats[:5], 1):
        print(f'Game {i}: {pattern} = {sum(pattern)}')
print('\nNote: Each round score is calculated from pairs of matching cards')