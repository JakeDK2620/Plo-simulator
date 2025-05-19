
import streamlit as st
import random
from itertools import combinations
from treys import Card, Evaluator

evaluator = Evaluator()
suits = ['s', 'h', 'd', 'c']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
deck = [r + s for r in ranks for s in suits]

def to_treys(cards):
    return [Card.new(c) for c in cards]

def plo_best_hand(hand, board):
    best = 7463
    for h in combinations(hand, 2):
        for b in combinations(board, 3):
            score = evaluator.evaluate(list(h), list(b))
            if score < best:
                best = score
    return best

def get_random_hand(exclude):
    available = list(set(deck) - set(exclude))
    return random.sample(available, 4)

def get_random_board(exclude, n):
    available = list(set(deck) - set(exclude))
    return random.sample(available, n)

def simulate(hero_hand, opponent_hands, board_cards, street, num_sims, randomize_opps):
    wins = ties = 0
    hero_treys = to_treys(hero_hand)
    board_base = to_treys(board_cards)
    needed = {'preflop': 5, 'flop': 2, 'turn': 1, 'river': 0}[street]

    for _ in range(num_sims):
        used = set(hero_hand + board_cards)
        sim_board = board_base + to_treys(get_random_board(used, needed))
        used.update(Card.int_to_str(c) for c in sim_board)

        current_opps = []
        for opp in opponent_hands:
            if randomize_opps or len(opp) != 4:
                hand = get_random_hand(used)
                used.update(hand)
                current_opps.append(to_treys(hand))
            else:
                current_opps.append(to_treys(opp))

        hero_score = plo_best_hand(hero_treys, sim_board)
        opp_scores = [plo_best_hand(opp, sim_board) for opp in current_opps]

        if all(hero_score < s for s in opp_scores):
            wins += 1
        elif any(hero_score == s for s in opp_scores):
            ties += 1

    return wins, ties, num_sims

# Streamlit UI
st.title("Pot Limit Omaha Simulator – 2 til 8 spillere")

num_players = st.slider("Antal spillere (inkl. Hero)", 2, 8, 4)
num_opponents = num_players - 1

hero_hand = st.multiselect("Vælg Hero's hånd (4 kort)", options=deck, max_selections=4)

board_choices = list(set(deck) - set(hero_hand))
board = st.multiselect("Vælg Board-kort (op til 5)", options=sorted(board_choices), max_selections=5)

opponent_hands = []
randomize_opps = st.checkbox("Brug tilfældige hænder for modstandere", value=True)
for i in range(num_opponents):
    if not randomize_opps:
        opp = st.multiselect(f"Modstander {i+1} hånd (4 kort)", options=deck, max_selections=4, key=f"opp_{i}")
    else:
        opp = []  # will be generated in simulate
    opponent_hands.append(opp)

street = st.selectbox("Street", ["preflop", "flop", "turn", "river"])
num_sims = st.slider("Antal simuleringer", 100, 20000, 1000)

if street == "preflop" and len(board) > 0:
    st.error("Du må ikke vælge boardkort ved preflop-simulering.")
elif street == "river" and len(board) < 5:
    st.error("River-simulering kræver præcis 5 boardkort.")
elif st.button("Kør simulering"):
    if len(hero_hand) != 4:
        st.error("Hero skal have præcis 4 kort.")
    elif not randomize_opps and any(len(opp) != 4 for opp in opponent_hands):
        st.error("Alle modstandere skal have 4 kort.")
    else:
        wins, ties, total = simulate(hero_hand, opponent_hands, board, street, num_sims, randomize_opps)
        st.success(f"Hero vinder: {wins}/{total} = {wins/total:.2%}")
        st.info(f"Split pot: {ties}/{total} = {ties/total:.2%}")
        st.warning(f"Hero taber: {(total - wins - ties)}/{total} = {(total - wins - ties)/total:.2%}")
