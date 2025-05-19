
import streamlit as st
import itertools
import random
import json
from treys import Card, Evaluator, Deck

evaluator = Evaluator()

def card_str_to_int(card_str):
    return Card.new(card_str)

def parse_hand(hand_strs):
    return [card_str_to_int(c) for c in hand_strs]

def flatten(hands):
    return [card for hand in hands for card in hand]

def generate_random_board(used_cards):
    deck = Deck()
    deck.cards = [card for card in deck.cards if card not in used_cards]
    return random.sample(deck.cards, 5)

def simulate(hero_hand, opponent_hands, board, street, num_simulations):
    wins = 0
    ties = 0
    total = 0

    for _ in range(num_simulations):
        used_cards = hero_hand + flatten(opponent_hands) + board
        sim_board = board.copy()

        if street == "Preflop":
            sim_board = generate_random_board(used_cards)
        elif street == "Flop":
            sim_board += random.sample([c for c in Deck().cards if c not in used_cards], 2)
        elif street == "Turn":
            sim_board += random.sample([c for c in Deck().cards if c not in used_cards], 1)

        hero_combos = list(itertools.combinations(hero_hand, 2))
        hero_best = min([evaluator.evaluate(h, sim_board) for h in hero_combos])

        opp_best_scores = []
        for opp in opponent_hands:
            opp_combos = list(itertools.combinations(opp, 2))
            opp_best = min([evaluator.evaluate(h, sim_board) for h in opp_combos])
            opp_best_scores.append(opp_best)

        if all(hero_best < opp for opp in opp_best_scores):
            wins += 1
        elif any(hero_best == opp for opp in opp_best_scores):
            ties += 1

        total += 1

    return wins, ties, total

# Streamlit UI placeholder
st.title("Pot Limit Omaha Simulator")

hero_input = st.text_input("Hero hånd (4 kort, fx 'AsKsQsJs'):")
opponent_input = st.text_area("Modstandere (hver linje = 4 kort, fx '9d8d7d6d'):")
board_input = st.text_input("Board kort (0–5 kort, fx 'AhKhQh'):")
street = st.selectbox("Street", ["Preflop", "Flop", "Turn", "River"])
num_simulations = st.slider("Antal simuleringer", 100, 20000, 1000)

if st.button("Kør simulering"):
    try:
        hero_hand = parse_hand([hero_input[i:i+2] for i in range(0, 8, 2)])
        opp_lines = opponent_input.strip().split("\n")
        opponent_hands = [parse_hand([line[i:i+2] for i in range(0, 8, 2)]) for line in opp_lines]
        board = parse_hand([board_input[i:i+2] for i in range(0, len(board_input), 2)]) if board_input else []

        wins, ties, total = simulate(hero_hand, opponent_hands, board, street, num_simulations)

        st.write(f"Hero wins: {wins} ({wins/total:.2%})")
        st.write(f"Ties: {ties} ({ties/total:.2%})")
        st.write(f"Losses: {total - wins - ties} ({(total - wins - ties)/total:.2%})")
    except Exception as e:
        st.error(f"Fejl i simulering: {str(e)}")
